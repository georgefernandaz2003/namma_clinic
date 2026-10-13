import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LabTestSelect, type LabTestItem, isPoctTest } from '../LabTestSelect';

const mockLabTests: LabTestItem[] = [
  {
    id: 1,
    code: 'L-HBA1C',
    name: 'HbA1c Glycated Hemoglobin',
    category: 'Diabetes',
    reference_range: '4.0 - 5.6 %',
    unit: '%'
  },
  {
    id: 2,
    code: 'L-RBG',
    name: 'Random Blood Glucose (Rapid Strip)',
    category: 'Diabetes',
    reference_range: '70 - 140 mg/dL',
    unit: 'mg/dL'
  },
  {
    id: 3,
    code: 'L-HB',
    name: 'Hemoglobin (Hb Estimation)',
    category: 'Hematology',
    reference_range: '12.0 - 15.5 g/dL',
    unit: 'g/dL'
  },
  {
    id: 4,
    code: 'L-DENGUE',
    name: 'Dengue NS1 Antigen Rapid Test Card',
    category: 'Serology',
    reference_range: 'Negative',
    unit: 'Result'
  },
  {
    id: 5,
    code: 'L-MALARIA',
    name: 'Malaria Antigen (Pf/Pv) Rapid Test',
    category: 'Serology',
    reference_range: 'Negative',
    unit: 'Result'
  },
  {
    id: 6,
    code: 'L-URINE-PROT',
    name: 'Urine Albumin / Protein Test',
    category: 'Urinalysis',
    reference_range: 'Nil / Negative',
    unit: 'Grade'
  },
  {
    id: 7,
    code: 'L-LFT',
    name: 'Liver Function Test (Bilirubin & LFT)',
    category: 'Biochemistry',
    reference_range: 'Bilirubin < 1.2 mg/dL',
    unit: 'mg/dL'
  }
];

describe('LabTestSelect Component', () => {
  it('correctly classifies POCT rapid tests vs Hub Lab tests', () => {
    expect(isPoctTest(mockLabTests[1])).toBe(true); // Random Blood Glucose Rapid Strip
    expect(isPoctTest(mockLabTests[3])).toBe(true); // Dengue Rapid Card
    expect(isPoctTest(mockLabTests[4])).toBe(true); // Malaria Rapid
    expect(isPoctTest(mockLabTests[5])).toBe(true); // Urine Albumin
    expect(isPoctTest(mockLabTests[0])).toBe(false); // HbA1c (Hub Lab)
    expect(isPoctTest(mockLabTests[6])).toBe(false); // LFT (Hub Lab)
  });

  it('renders dropdown trigger and opens dropdown on click', () => {
    const handleChange = vi.fn();
    render(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[]}
        onChange={handleChange}
      />
    );

    expect(screen.getByText(/Order 14 Essential Diagnostic Tests/i)).toBeDefined();
    expect(screen.getByText(/0 \/ 7 Selected/i)).toBeDefined();

    const trigger = screen.getByTestId('lab-test-dropdown-trigger');
    fireEvent.click(trigger);

    expect(screen.getByTestId('lab-test-dropdown-menu')).toBeDefined();
    expect(screen.getByPlaceholderText(/Search 14 tests by name/i)).toBeDefined();
    expect(screen.getByText('HbA1c Glycated Hemoglobin')).toBeDefined();
    expect(screen.getByText('Dengue NS1 Antigen Rapid Test Card')).toBeDefined();
  });

  it('filters tests by search query (name, code, or POCT/Hub keyword)', () => {
    const handleChange = vi.fn();
    render(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[]}
        onChange={handleChange}
      />
    );

    // Open dropdown
    fireEvent.click(screen.getByTestId('lab-test-dropdown-trigger'));

    const searchInput = screen.getByTestId('lab-test-search-input');
    fireEvent.change(searchInput, { target: { value: 'Dengue' } });

    expect(screen.getByText('Dengue NS1 Antigen Rapid Test Card')).toBeDefined();
    expect(screen.queryByText('HbA1c Glycated Hemoglobin')).toBeNull();

    // Search by code
    fireEvent.change(searchInput, { target: { value: 'L-HBA1C' } });
    expect(screen.getByText('HbA1c Glycated Hemoglobin')).toBeDefined();
    expect(screen.queryByText('Dengue NS1 Antigen Rapid Test Card')).toBeNull();
  });

  it('toggles selection when clicking a test row', () => {
    const handleChange = vi.fn();
    const { rerender } = render(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[]}
        onChange={handleChange}
      />
    );

    fireEvent.click(screen.getByTestId('lab-test-dropdown-trigger'));
    const testOption = screen.getByTestId('lab-test-option-1');
    fireEvent.click(testOption);

    expect(handleChange).toHaveBeenCalledWith([1]);

    // Now re-render with test 1 selected
    rerender(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[1]}
        onChange={handleChange}
      />
    );

    // Clicking test 1 again deselects it
    fireEvent.click(screen.getByTestId('lab-test-option-1'));
    expect(handleChange).toHaveBeenCalledWith([]);
  });

  it('renders dismissible chips for selected tests and removes them on chip delete click', () => {
    const handleChange = vi.fn();
    render(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[1, 4]} // HbA1c & Dengue
        onChange={handleChange}
      />
    );

    // Chips rendered outside dropdown
    expect(screen.getByTestId('selected-tests-chips')).toBeDefined();
    expect(screen.getByText('HbA1c Glycated Hemoglobin')).toBeDefined();
    expect(screen.getByText('Dengue NS1 Antigen Rapid Test Card')).toBeDefined();

    const removeBtn = screen.getByRole('button', { name: /Remove Dengue NS1 Antigen/i });
    fireEvent.click(removeBtn);

    expect(handleChange).toHaveBeenCalledWith([1]);
  });

  it('supports Select All and Clear All actions', () => {
    const handleChange = vi.fn();
    const { rerender } = render(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[]}
        onChange={handleChange}
      />
    );

    const selectAllBtn = screen.getByRole('button', { name: /Select All 14/i });
    fireEvent.click(selectAllBtn);
    expect(handleChange).toHaveBeenCalledWith([1, 2, 3, 4, 5, 6, 7]);

    // Rerender with all selected
    rerender(
      <LabTestSelect
        availableTests={mockLabTests}
        selectedIds={[1, 2, 3, 4, 5, 6, 7]}
        onChange={handleChange}
      />
    );

    const clearAllBtn = screen.getByRole('button', { name: /Clear All/i });
    fireEvent.click(clearAllBtn);
    expect(handleChange).toHaveBeenCalledWith([]);
  });
});
