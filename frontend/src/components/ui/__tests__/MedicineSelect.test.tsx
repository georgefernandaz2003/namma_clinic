import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MedicineSelect } from '../MedicineSelect';
import type { MedicineMaster } from '../../../types';

const mockMedicines: MedicineMaster[] = [
  {
    id: 1,
    generic_name: 'Paracetamol',
    brand_name: 'Dolo 650',
    strength: '650 mg',
    dosage_form: 'Tablet',
    unit: 'Tablets',
    category: 'Analgesic',
    minimum_stock: 50,
    reorder_level: 100,
    available_stock: 250,
    stock_status: 'NORMAL'
  },
  {
    id: 2,
    generic_name: 'Metformin HCl',
    brand_name: 'Glycomet',
    strength: '500 mg',
    dosage_form: 'Tablet',
    unit: 'Tablets',
    category: 'Anti-Diabetic',
    minimum_stock: 50,
    reorder_level: 100,
    available_stock: 0,
    stock_status: 'OUT_OF_STOCK'
  },
  {
    id: 3,
    generic_name: 'Amoxicillin Trihydrate',
    brand_name: 'Mox',
    strength: '500 mg',
    dosage_form: 'Capsule',
    unit: 'Capsules',
    category: 'Antibiotic',
    minimum_stock: 30,
    reorder_level: 60,
    available_stock: 80,
    stock_status: 'NORMAL'
  }
];

describe('MedicineSelect Component', () => {
  it('renders input with placeholder and opens inventory dropdown on focus', () => {
    const handleChange = vi.fn();
    render(
      <MedicineSelect
        value=""
        medicines={mockMedicines}
        onChange={handleChange}
      />
    );

    const input = screen.getByPlaceholderText(/Search & select EDL medicine/i);
    expect(input).toBeDefined();

    fireEvent.focus(input);
    expect(screen.getByText(/Facility EDL Medicines Inventory/i)).toBeDefined();
    expect(screen.getByText('Paracetamol')).toBeDefined();
    expect(screen.getByText('Metformin HCl')).toBeDefined();
  });

  it('filters medicines by generic name, brand name, and category', () => {
    const handleChange = vi.fn();
    render(
      <MedicineSelect
        value=""
        medicines={mockMedicines}
        onChange={handleChange}
      />
    );

    const input = screen.getByPlaceholderText(/Search & select EDL medicine/i);
    fireEvent.change(input, { target: { value: 'Dolo' } });

    expect(screen.getByText('Paracetamol')).toBeDefined();
    expect(screen.queryByText('Metformin HCl')).toBeNull();
  });

  it('displays stock indicator badge when medicine is selected', () => {
    const handleChange = vi.fn();
    render(
      <MedicineSelect
        value="Paracetamol 650 mg Tablet"
        medicineId={1}
        medicines={mockMedicines}
        onChange={handleChange}
      />
    );

    expect(screen.getByText(/In Stock: 250 Tablets \(FEFO Ready\)/i)).toBeDefined();
  });

  it('selects medicine and calls onChange with id and formatted name', () => {
    const handleChange = vi.fn();
    render(
      <MedicineSelect
        value=""
        medicines={mockMedicines}
        onChange={handleChange}
      />
    );

    const input = screen.getByPlaceholderText(/Search & select EDL medicine/i);
    fireEvent.focus(input);

    const medOption = screen.getByText('Amoxicillin Trihydrate');
    fireEvent.mouseDown(medOption);

    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        medicine_id: 3,
        medicine_name: 'Amoxicillin Trihydrate 500 mg Capsule'
      })
    );
  });

  it('allows prescribing custom non-EDL medicine when not found in inventory', () => {
    const handleChange = vi.fn();
    render(
      <MedicineSelect
        value=""
        medicines={mockMedicines}
        onChange={handleChange}
      />
    );

    const input = screen.getByPlaceholderText(/Search & select EDL medicine/i);
    fireEvent.change(input, { target: { value: 'Vitamin C Chewable' } });

    const customOption = screen.getByText(/Prescribe custom \/ non-EDL:/i);
    expect(customOption).toBeDefined();
    fireEvent.mouseDown(customOption);

    expect(handleChange).toHaveBeenCalledWith({
      medicine_name: 'Vitamin C Chewable'
    });
  });
});
