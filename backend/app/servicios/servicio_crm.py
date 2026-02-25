"""
Servicio CRM: Lógica de negocio para gestión de pipelines, deals y activities.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..datos.esquemas import CrmActivityCreate, CrmDealCreate, CrmDealUpdate, CrmPipelineCreate, CrmPipelineUpdate
from ..datos.modelos_crm import CrmActivity, CrmDeal, CrmPipeline, CrmStage, EstadoDeal, TipoActividadCRM


class ServicioCRM:
    """Servicio para gestión de CRM."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # PIPELINES
    # =========================================================================

    def listar_pipelines(self, tenant_id: UUID) -> List[CrmPipeline]:
        """Lista pipelines del tenant con sus stages (eager load)."""
        return (
            self.db.query(CrmPipeline)
            .filter(CrmPipeline.tenant_id == tenant_id, CrmPipeline.deleted_at is None)
            .options(joinedload(CrmPipeline.etapas))
            .order_by(CrmPipeline.es_default.desc(), CrmPipeline.nombre)
            .all()
        )

    def obtener_pipeline(self, pipeline_id: UUID, tenant_id: UUID) -> Optional[CrmPipeline]:
        """Obtiene un pipeline por ID."""
        return (
            self.db.query(CrmPipeline)
            .filter(CrmPipeline.id == pipeline_id, CrmPipeline.tenant_id == tenant_id, CrmPipeline.deleted_at is None)
            .options(joinedload(CrmPipeline.etapas))
            .first()
        )

    def crear_pipeline(self, tenant_id: UUID, data: CrmPipelineCreate) -> CrmPipeline:
        """Crea un nuevo pipeline. Si es_default=True, quita default de otros."""
        # Si es default, quitar default de los demás
        if data.es_default:
            self.db.query(CrmPipeline).filter(CrmPipeline.tenant_id == tenant_id, CrmPipeline.es_default).update(
                {"es_default": False}
            )

        pipeline = CrmPipeline(tenant_id=tenant_id, **data.model_dump())
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def actualizar_pipeline(self, pipeline_id: UUID, tenant_id: UUID, data: CrmPipelineUpdate) -> Optional[CrmPipeline]:
        """Actualiza un pipeline."""
        pipeline = self.obtener_pipeline(pipeline_id, tenant_id)
        if not pipeline:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pipeline, key, value)

        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def eliminar_pipeline(self, pipeline_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete de pipeline. Valida que no tenga deals activos."""
        pipeline = self.obtener_pipeline(pipeline_id, tenant_id)
        if not pipeline:
            return False

        # Validar que no tenga deals activos
        deals_count = (
            self.db.query(func.count(CrmDeal.id))
            .filter(
                CrmDeal.pipeline_id == pipeline_id,
                CrmDeal.tenant_id == tenant_id,
                CrmDeal.deleted_at is None,
                CrmDeal.estado_cierre == EstadoDeal.ABIERTO,
            )
            .scalar()
        )

        if deals_count > 0:
            raise ValueError(f"No se puede eliminar: hay {deals_count} deals activos en este pipeline")

        pipeline.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    # =========================================================================
    # DEALS
    # =========================================================================

    def listar_deals(self, tenant_id: UUID, filters: Optional[Dict[str, Any]] = None) -> List[CrmDeal]:
        """Lista deals con filtros opcionales. Eager load: tercero, usuario, stage."""
        query = (
            self.db.query(CrmDeal)
            .filter(CrmDeal.tenant_id == tenant_id, CrmDeal.deleted_at is None)
            .options(joinedload(CrmDeal.tercero), joinedload(CrmDeal.usuario), joinedload(CrmDeal.stage))
        )

        if filters:
            if "pipeline_id" in filters:
                query = query.filter(CrmDeal.pipeline_id == filters["pipeline_id"])
            if "stage_id" in filters:
                query = query.filter(CrmDeal.stage_id == filters["stage_id"])
            if "usuario_id" in filters:
                query = query.filter(CrmDeal.usuario_id == filters["usuario_id"])
            if "estado_cierre" in filters:
                query = query.filter(CrmDeal.estado_cierre == filters["estado_cierre"])

        return query.order_by(CrmDeal.created_at.desc()).all()

    def obtener_deal(self, deal_id: UUID, tenant_id: UUID) -> Optional[CrmDeal]:
        """Obtiene un deal por ID con relaciones cargadas."""
        return (
            self.db.query(CrmDeal)
            .filter(CrmDeal.id == deal_id, CrmDeal.tenant_id == tenant_id, CrmDeal.deleted_at is None)
            .options(
                joinedload(CrmDeal.tercero),
                joinedload(CrmDeal.usuario),
                joinedload(CrmDeal.stage),
                joinedload(CrmDeal.pipeline),
            )
            .first()
        )

    def crear_deal(self, tenant_id: UUID, data: CrmDealCreate, usuario_id: UUID) -> CrmDeal:
        """Crea un nuevo deal. Valida tercero y stage. Log activity automática."""
        # Validar tercero existe y pertenece al tenant
        from ..datos.modelos import Terceros

        tercero = (
            self.db.query(Terceros).filter(Terceros.id == data.tercero_id, Terceros.tenant_id == tenant_id).first()
        )
        if not tercero:
            raise ValueError("Tercero no encontrado")

        # Validar stage existe y pertenece al pipeline
        stage = (
            self.db.query(CrmStage)
            .filter(
                CrmStage.id == data.stage_id, CrmStage.pipeline_id == data.pipeline_id, CrmStage.tenant_id == tenant_id
            )
            .first()
        )
        if not stage:
            raise ValueError("Stage no encontrado o no pertenece al pipeline")

        # Crear deal
        deal = CrmDeal(tenant_id=tenant_id, **data.model_dump())
        self.db.add(deal)
        self.db.flush()

        # Log activity automática
        activity = CrmActivity(
            tenant_id=tenant_id,
            deal_id=deal.id,
            usuario_id=usuario_id,
            tipo=TipoActividadCRM.NOTA,
            asunto="Deal creado",
            contenido=f"Deal '{deal.nombre}' creado en stage '{stage.nombre}'",
            fecha_actividad=datetime.now(timezone.utc),
            es_automatica=True,
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(deal)
        return deal

    def actualizar_deal(self, deal_id: UUID, tenant_id: UUID, data: CrmDealUpdate) -> Optional[CrmDeal]:
        """Actualiza datos de un deal."""
        deal = self.obtener_deal(deal_id, tenant_id)
        if not deal:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(deal, key, value)

        deal.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(deal)
        return deal

    def mover_deal(self, deal_id: UUID, nuevo_stage_id: UUID, tenant_id: UUID, usuario_id: UUID) -> CrmDeal:
        """Mueve deal a otro stage. Log activity automática."""
        deal = self.obtener_deal(deal_id, tenant_id)
        if not deal:
            raise ValueError("Deal no encontrado")

        # Validar nuevo stage
        nuevo_stage = (
            self.db.query(CrmStage).filter(CrmStage.id == nuevo_stage_id, CrmStage.tenant_id == tenant_id).first()
        )
        if not nuevo_stage:
            raise ValueError("Stage no encontrado")

        stage_anterior = deal.stage.nombre
        deal.stage_id = nuevo_stage_id
        deal.updated_at = datetime.now(timezone.utc)

        # Log activity automática
        activity = CrmActivity(
            tenant_id=tenant_id,
            deal_id=deal.id,
            usuario_id=usuario_id,
            tipo=TipoActividadCRM.NOTA,
            asunto="Deal movido",
            contenido=f"Movido de '{stage_anterior}' a '{nuevo_stage.nombre}'",
            fecha_actividad=datetime.now(timezone.utc),
            es_automatica=True,
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(deal)
        return deal

    def cerrar_deal(
        self, deal_id: UUID, estado_cierre: EstadoDeal, motivo: Optional[str], tenant_id: UUID, usuario_id: UUID
    ) -> CrmDeal:
        """Cierra un deal (GANADO/PERDIDO/ABANDONADO). Log activity."""
        deal = self.obtener_deal(deal_id, tenant_id)
        if not deal:
            raise ValueError("Deal no encontrado")

        deal.estado_cierre = estado_cierre
        if motivo:
            deal.motivo_perdida = motivo
        deal.updated_at = datetime.now(timezone.utc)

        # Log activity
        activity = CrmActivity(
            tenant_id=tenant_id,
            deal_id=deal.id,
            usuario_id=usuario_id,
            tipo=TipoActividadCRM.NOTA,
            asunto=f"Deal {estado_cierre.value}",
            contenido=motivo or f"Deal marcado como {estado_cierre.value}",
            fecha_actividad=datetime.now(timezone.utc),
            es_automatica=True,
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(deal)
        return deal

    def eliminar_deal(self, deal_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete de deal."""
        deal = self.obtener_deal(deal_id, tenant_id)
        if not deal:
            return False

        deal.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    # =========================================================================
    # ACTIVITIES
    # =========================================================================

    def crear_actividad(self, tenant_id: UUID, data: CrmActivityCreate, usuario_id: UUID) -> CrmActivity:
        """Crea una activity. Actualiza fecha_ultimo_contacto del deal."""
        # Validar deal existe
        deal = self.obtener_deal(data.deal_id, tenant_id)
        if not deal:
            raise ValueError("Deal no encontrado")

        activity = CrmActivity(tenant_id=tenant_id, usuario_id=usuario_id, **data.model_dump())
        self.db.add(activity)

        # Actualizar fecha_ultimo_contacto del deal
        deal.fecha_ultimo_contacto = activity.fecha_actividad
        deal.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def listar_actividades(self, deal_id: UUID, tenant_id: UUID) -> List[CrmActivity]:
        """Lista activities de un deal. Order by fecha DESC."""
        return (
            self.db.query(CrmActivity)
            .filter(CrmActivity.deal_id == deal_id, CrmActivity.tenant_id == tenant_id, CrmActivity.deleted_at is None)
            .options(joinedload(CrmActivity.usuario))
            .order_by(CrmActivity.fecha_actividad.desc())
            .all()
        )

    def eliminar_actividad(self, activity_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete de activity."""
        activity = (
            self.db.query(CrmActivity).filter(CrmActivity.id == activity_id, CrmActivity.tenant_id == tenant_id).first()
        )
        if not activity:
            return False

        activity.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
