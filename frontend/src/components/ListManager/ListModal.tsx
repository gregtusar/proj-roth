import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalButton,
  SIZE,
  ROLE,
} from 'baseui/modal';
import { Input } from 'baseui/input';
import { Textarea } from 'baseui/textarea';
import { FormControl } from 'baseui/form-control';
import { AppDispatch } from '../../store';
import { createList, setModalOpen } from '../../store/listsSlice';

const ListModal: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [query, setQuery] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleClose = () => {
    dispatch(setModalOpen(false));
    setName('');
    setDescription('');
    setQuery('');
    setErrors({});
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!name.trim()) {
      newErrors.name = 'List name is required';
    }
    
    if (!query.trim()) {
      newErrors.query = 'SQL query is required';
    } else if (!query.toLowerCase().startsWith('select')) {
      newErrors.query = 'Query must be a SELECT statement';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;

    try {
      await dispatch(
        createList({
          name: name.trim(),
          description: description.trim(),
          query: query.trim(),
        })
      ).unwrap();
      handleClose();
    } catch (error) {
      setErrors({ submit: 'Failed to create list. Please try again.' });
    }
  };

  return (
    <Modal
      onClose={handleClose}
      isOpen
      animate
      autoFocus
      size={SIZE.default}
      role={ROLE.dialog}
    >
      <ModalHeader>Create New List</ModalHeader>
      <ModalBody>
        <FormControl
          label="List Name"
          error={errors.name}
          caption="Give your list a descriptive name"
        >
          <Input
            value={name}
            onChange={(e) => setName((e.target as HTMLInputElement).value)}
            placeholder="e.g., High Propensity Democrats"
            error={!!errors.name}
          />
        </FormControl>

        <FormControl
          label="Description (Optional)"
          caption="Add a description to help you remember this list's purpose"
        >
          <Textarea
            value={description}
            onChange={(e) => setDescription((e.target as HTMLTextAreaElement).value)}
            placeholder="e.g., Democrats who voted in the last 3 elections"
            rows={3}
          />
        </FormControl>

        <FormControl
          label="SQL Query"
          error={errors.query}
          caption="Enter a SELECT query to define this list"
        >
          <Textarea
            value={query}
            onChange={(e) => setQuery((e.target as HTMLTextAreaElement).value)}
            placeholder="SELECT * FROM `proj-roth.voter_data.voters` WHERE demo_party = 'DEM' LIMIT 1000"
            rows={8}
            error={!!errors.query}
            overrides={{
              Input: {
                style: {
                  fontFamily: 'monospace',
                  fontSize: '13px',
                },
              },
            }}
          />
        </FormControl>

        {errors.submit && (
          <div style={{ color: 'red', marginTop: '10px' }}>{errors.submit}</div>
        )}
      </ModalBody>
      <ModalFooter>
        <ModalButton kind="tertiary" onClick={handleClose}>
          Cancel
        </ModalButton>
        <ModalButton onClick={handleSave}>Create List</ModalButton>
      </ModalFooter>
    </Modal>
  );
};

export default ListModal;