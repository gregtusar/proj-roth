import React from 'react';
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalButton,
  ROLE,
  SIZE,
} from 'baseui/modal';
import { KIND as ButtonKind } from 'baseui/button';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isLoading = false,
}) => {
  return (
    <Modal
      onClose={onClose}
      closeable
      isOpen={isOpen}
      animate
      autoFocus
      size={SIZE.default}
      role={ROLE.dialog}
    >
      <ModalHeader>{title}</ModalHeader>
      <ModalBody>{message}</ModalBody>
      <ModalFooter>
        <ModalButton kind={ButtonKind.tertiary} onClick={onClose}>
          {cancelText}
        </ModalButton>
        <ModalButton 
          onClick={onConfirm} 
          isLoading={isLoading}
          overrides={{
            BaseButton: {
              style: {
                backgroundColor: '#dc2626',
                ':hover': {
                  backgroundColor: '#b91c1c',
                },
              },
            },
          }}
        >
          {confirmText}
        </ModalButton>
      </ModalFooter>
    </Modal>
  );
};

export default ConfirmModal;