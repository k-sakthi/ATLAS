"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

interface CutContextType {
  currentCut: number;
  setCurrentCut: (cut: number) => void;
  availableCuts: number[];
}

const CutContext = createContext<CutContextType | undefined>(undefined);

export function CutProvider({ children }: { children: ReactNode }) {
  const [currentCut, setCurrentCut] = useState<number>(5); // Default to a valid cut for demo, let's say 5 or fetch dynamically
  const availableCuts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]; // Realistically fetch this or hardcode max based on test data

  return (
    <CutContext.Provider value={{ currentCut, setCurrentCut, availableCuts }}>
      {children}
    </CutContext.Provider>
  );
}

export function useCut() {
  const context = useContext(CutContext);
  if (context === undefined) {
    throw new Error("useCut must be used within a CutProvider");
  }
  return context;
}
