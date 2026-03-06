import { useState } from 'react';
import MarcaTab from '../components/config/MarcaTab';

type Tab = 'general' | 'marca';

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState<Tab>('general');

  return (
    <div>
      <h1 className="font-brand text-xl font-medium cv-text mb-6">Configuracion</h1>

      {/* Tab pills */}
      <div className="flex gap-2 mb-6">
        {(['general', 'marca'] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`cv-badge cursor-pointer capitalize ${
              activeTab === tab ? 'cv-badge-primary' : 'cv-badge-neutral'
            }`}
          >
            {tab === 'general' ? 'General' : 'Marca'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'general' && (
        <div className="cv-card p-12 text-center cv-muted">
          <p className="text-lg mb-2">Ajustes generales</p>
          <p className="text-sm">Proximamente: empresa, usuarios y suscripcion</p>
        </div>
      )}
      {activeTab === 'marca' && <MarcaTab />}
    </div>
  );
}
