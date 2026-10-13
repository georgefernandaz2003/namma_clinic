import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ICD10Select, parseDiagnosesFromProps, serializeDiagnoses } from '../ICD10Select';

describe('ICD10Select Component - Multi-Select Diagnosis', () => {
  it('parses and serializes single and multiple diagnoses accurately', () => {
    // Single code
    const single = parseDiagnosesFromProps('I10', 'Essential (Primary) Hypertension');
    expect(single).toHaveLength(1);
    expect(single[0].code).toBe('I10');
    expect(single[0].name).toBe('Essential (Primary) Hypertension');

    // Multiple codes with comma
    const multiple = parseDiagnosesFromProps('E11.9, I10', 'Type 2 Diabetes Mellitus without Complications, Essential (Primary) Hypertension');
    expect(multiple).toHaveLength(2);
    expect(multiple[0].code).toBe('E11.9');
    expect(multiple[1].code).toBe('I10');

    // Serialization
    const serialized = serializeDiagnoses(multiple);
    expect(serialized.code).toBe('E11.9, I10');
    expect(serialized.name).toContain('Type 2 Diabetes Mellitus without Complications');
    expect(serialized.name).toContain('Essential (Primary) Hypertension');
  });

  it('renders with multi-select label and handles selecting one or more diagnoses', () => {
    const handleChange = vi.fn();
    const { rerender } = render(
      <ICD10Select
        value=""
        code=""
        onChange={handleChange}
        required
      />
    );

    // Label should indicate multi-select
    expect(screen.getByText(/Select One or More/i)).toBeDefined();

    const input = screen.getByPlaceholderText(/Search & select ICD-10 diagnosis/i);
    fireEvent.focus(input);

    // Dropdown header should indicate multiple selection
    expect(screen.getByText(/Click item to toggle selection/i)).toBeDefined();

    // Select first diagnosis (e.g. Type 2 Diabetes)
    const option1 = screen.getByText('Type 2 Diabetes Mellitus without Complications');
    fireEvent.mouseDown(option1);

    expect(handleChange).toHaveBeenCalledWith(
      expect.stringContaining('E11.9'),
      expect.stringContaining('Type 2 Diabetes Mellitus without Complications')
    );

    // Re-render with first selection active
    rerender(
      <ICD10Select
        value="Type 2 Diabetes Mellitus without Complications"
        code="E11.9"
        onChange={handleChange}
        required
      />
    );

    // Should display selected chip
    expect(screen.getByText('1 diagnosis selected')).toBeDefined();
    expect(screen.getAllByText('E11.9').length).toBeGreaterThanOrEqual(1);

    // Now select second diagnosis (e.g. Essential Hypertension)
    fireEvent.focus(input);
    const option2 = screen.getByText('Essential (Primary) Hypertension');
    fireEvent.mouseDown(option2);

    // Should now contain BOTH codes
    expect(handleChange).toHaveBeenLastCalledWith(
      'E11.9, I10',
      expect.stringContaining('Essential (Primary) Hypertension')
    );
  });

  it('allows unselecting an existing diagnosis by clicking it again or clicking X on chip', () => {
    const handleChange = vi.fn();
    render(
      <ICD10Select
        value="Type 2 Diabetes Mellitus without Complications, Essential (Primary) Hypertension"
        code="E11.9, I10"
        onChange={handleChange}
      />
    );

    // Displays 2 chips
    expect(screen.getByText('2 diagnoses selected')).toBeDefined();
    expect(screen.getByText('E11.9')).toBeDefined();
    expect(screen.getByText('I10')).toBeDefined();

    // Remove first chip via X button
    const removeBtn = screen.getByLabelText('Remove Type 2 Diabetes Mellitus without Complications');
    fireEvent.click(removeBtn);

    expect(handleChange).toHaveBeenCalledWith('I10', expect.stringContaining('Hypertension'));
  });

  it('supports clear all button when multiple are selected', () => {
    const handleChange = vi.fn();
    render(
      <ICD10Select
        value="Type 2 Diabetes Mellitus without Complications, Essential (Primary) Hypertension"
        code="E11.9, I10"
        onChange={handleChange}
      />
    );

    const clearAllBtn = screen.getByTitle('Clear all selected diagnoses');
    fireEvent.click(clearAllBtn);

    expect(handleChange).toHaveBeenCalledWith('', '');
  });

  it('allows adding a custom diagnosis', () => {
    const handleChange = vi.fn();
    render(
      <ICD10Select
        value=""
        code=""
        onChange={handleChange}
      />
    );

    const input = screen.getByPlaceholderText(/Search & select ICD-10 diagnosis/i);
    fireEvent.change(input, { target: { value: 'Custom Acute Condition' } });

    // Should show "Add custom"
    const customOption = screen.getByText(/Add custom:/i);
    expect(customOption).toBeDefined();
    fireEvent.mouseDown(customOption);

    expect(handleChange).toHaveBeenCalledWith('R69', 'Custom Acute Condition');
  });
});
