interface StepProgressProps {
  currentStep: number;
  totalSteps: number;
  completedSteps: number[];
}

const STEP_LABELS = [
  'Primer producto',
  'Primera receta',
  'Primera venta',
  'Dashboard',
  'Primer cliente',
];

export default function StepProgress({ currentStep, totalSteps, completedSteps }: StepProgressProps) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: totalSteps }, (_, i) => {
        const step = i + 1;
        const isCompleted = completedSteps.includes(step);
        const isCurrent = step === currentStep;

        return (
          <div key={step} className="flex items-center gap-1.5">
            <div className="flex flex-col items-center">
              <div
                className={`flex items-center justify-center h-8 w-8 rounded-full text-xs font-semibold transition-all ${
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : isCurrent
                      ? 'bg-primary-500 text-white ring-2 ring-primary-200'
                      : 'bg-gray-100 text-gray-400'
                }`}
              >
                {isCompleted ? '✓' : step}
              </div>
              <span className="text-[10px] text-gray-500 mt-1 text-center max-w-[60px] leading-tight hidden sm:block">
                {STEP_LABELS[i]}
              </span>
            </div>
            {i < totalSteps - 1 && (
              <div className={`w-6 h-0.5 mb-4 sm:mb-0 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
