import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

export type ModelType = 'funk_svd' | 'item_knn';

interface ModelContextValue {
  selectedModel: ModelType;
  setSelectedModel: (model: ModelType) => void;
  toggleModel: () => void;
  modelDisplayName: string;
}

const ModelContext = createContext<ModelContextValue | undefined>(undefined);

export const ModelProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedModel, setSelectedModel] = useState<ModelType>(() => {
    const saved = localStorage.getItem('cinematch_active_model');
    return saved === 'item_knn' ? 'item_knn' : 'funk_svd';
  });

  useEffect(() => {
    localStorage.setItem('cinematch_active_model', selectedModel);
  }, [selectedModel]);

  const toggleModel = () => {
    setSelectedModel((prev) => (prev === 'funk_svd' ? 'item_knn' : 'funk_svd'));
  };

  const modelDisplayName =
    selectedModel === 'funk_svd' ? 'Funk-SVD (Biased SGD)' : 'Item-KNN (Adjusted Cosine)';

  return (
    <ModelContext.Provider
      value={{
        selectedModel,
        setSelectedModel,
        toggleModel,
        modelDisplayName,
      }}
    >
      {children}
    </ModelContext.Provider>
  );
};

export function useModel(): ModelContextValue {
  const context = useContext(ModelContext);
  if (!context) {
    throw new Error('useModel must be used within a ModelProvider');
  }
  return context;
}
