import React, { createContext, useContext, useState, useRef, useCallback } from 'react';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import type { ConfirmVariant, ConfirmDetailItem } from '../components/ui/ConfirmDialog';

export interface ConfirmOptions {
  title: string;
  message: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  details?: ConfirmDetailItem[];
  warning?: string;
  loadingText?: string;
  onConfirm?: () => Promise<void> | void;
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
  closeConfirmation: () => void;
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined);

export const ConfirmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [dialogState, setDialogState] = useState<{
    open: boolean;
    title: string;
    message: React.ReactNode;
    confirmText?: string;
    cancelText?: string;
    variant?: ConfirmVariant;
    details?: ConfirmDetailItem[];
    warning?: string;
    loadingText?: string;
    loading: boolean;
    error: string | null;
  }>({
    open: false,
    title: '',
    message: '',
    loading: false,
    error: null,
  });

  const resolverRef = useRef<((value: boolean) => void) | null>(null);
  const onConfirmHandlerRef = useRef<(() => Promise<void> | void) | null>(null);
  const isExecutingRef = useRef<boolean>(false);

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      resolverRef.current = resolve;
      onConfirmHandlerRef.current = options.onConfirm || null;
      isExecutingRef.current = false;

      setDialogState({
        open: true,
        title: options.title,
        message: options.message,
        confirmText: options.confirmText,
        cancelText: options.cancelText,
        variant: options.variant || 'primary',
        details: options.details,
        warning: options.warning,
        loadingText: options.loadingText,
        loading: false,
        error: null,
      });
    });
  }, []);

  const closeConfirmation = useCallback(() => {
    if (resolverRef.current) {
      resolverRef.current(false);
      resolverRef.current = null;
    }
    onConfirmHandlerRef.current = null;
    isExecutingRef.current = false;
    setDialogState((prev) => ({ ...prev, open: false, loading: false, error: null }));
  }, []);

  const handleConfirmAction = async () => {
    // Prevent double submission
    if (isExecutingRef.current) return;

    if (onConfirmHandlerRef.current) {
      try {
        isExecutingRef.current = true;
        setDialogState((prev) => ({ ...prev, loading: true, error: null }));
        
        await onConfirmHandlerRef.current();

        // If successful, close and resolve true
        if (resolverRef.current) {
          resolverRef.current(true);
          resolverRef.current = null;
        }
        setDialogState((prev) => ({ ...prev, open: false, loading: false, error: null }));
      } catch (err: any) {
        // Extract descriptive error
        const errorMsg =
          err?.response?.data?.error ||
          err?.response?.data?.detail ||
          (typeof err?.response?.data === 'string' ? err.response.data : null) ||
          err?.message ||
          'Operation failed. Please check inputs and retry.';
        
        setDialogState((prev) => ({
          ...prev,
          loading: false,
          error: errorMsg,
        }));
      } finally {
        isExecutingRef.current = false;
      }
    } else {
      if (resolverRef.current) {
        resolverRef.current(true);
        resolverRef.current = null;
      }
      setDialogState((prev) => ({ ...prev, open: false, loading: false, error: null }));
    }
  };

  return (
    <ConfirmContext.Provider value={{ confirm, closeConfirmation }}>
      {children}
      <ConfirmDialog
        open={dialogState.open}
        title={dialogState.title}
        message={dialogState.message}
        confirmText={dialogState.confirmText}
        cancelText={dialogState.cancelText}
        variant={dialogState.variant}
        details={dialogState.details}
        warning={dialogState.warning}
        loading={dialogState.loading}
        loadingText={dialogState.loadingText}
        error={dialogState.error}
        onConfirm={handleConfirmAction}
        onCancel={closeConfirmation}
      />
    </ConfirmContext.Provider>
  );
};

export const useConfirm = () => {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider');
  }
  return context;
};
