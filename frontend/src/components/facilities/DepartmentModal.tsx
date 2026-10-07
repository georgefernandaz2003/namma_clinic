import React, { useState, useEffect, useCallback } from 'react';
import { X, Layers, Plus, Pencil, Trash2, Check, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';
import type { Facility, Department } from '../../types';
import { fetchDepartments, createDepartment, updateDepartment, deleteDepartment } from '../../api/departments';

interface DepartmentModalProps {
  isOpen: boolean;
  facility: Facility | null;
  onClose: () => void;
}

export const DepartmentModal: React.FC<DepartmentModalProps> = ({ isOpen, facility, onClose }) => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // New Department Form State
  const [isAdding, setIsAdding] = useState<boolean>(false);
  const [newCode, setNewCode] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [newActive, setNewActive] = useState<boolean>(true);

  // Edit Department State
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editActive, setEditActive] = useState<boolean>(true);

  const loadDepartments = useCallback(async () => {
    if (!facility) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchDepartments(facility.id);
      setDepartments(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load facility departments.');
    } finally {
      setIsLoading(false);
    }
  }, [facility]);

  useEffect(() => {
    if (isOpen && facility) {
      setFeedback(null);
      setError(null);
      setIsAdding(false);
      setEditingId(null);
      loadDepartments();
    }
  }, [isOpen, facility, loadDepartments]);

  if (!isOpen || !facility) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCode.trim() || !newName.trim()) {
      setError('Department Code and Name are required.');
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await createDepartment({
        facility: facility.id,
        code: newCode.trim().toUpperCase(),
        name: newName.trim(),
        is_active: newActive,
      });
      setFeedback(`Department "${newName.trim()}" [${newCode.trim().toUpperCase()}] created successfully.`);
      setNewCode('');
      setNewName('');
      setNewActive(true);
      setIsAdding(false);
      await loadDepartments();
    } catch (err: any) {
      setError(err?.message || 'Failed to create department.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartEdit = (dept: Department) => {
    setEditingId(dept.id);
    setEditName(dept.name);
    setEditActive(dept.is_active);
    setError(null);
  };

  const handleSaveEdit = async (deptId: number) => {
    if (!editName.trim()) {
      setError('Department Name cannot be empty.');
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await updateDepartment(deptId, {
        name: editName.trim(),
        is_active: editActive,
      });
      setFeedback(`Department updated successfully.`);
      setEditingId(null);
      await loadDepartments();
    } catch (err: any) {
      setError(err?.message || 'Failed to update department.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (dept: Department) => {
    if (!window.confirm(`Are you sure you want to delete department "${dept.name}" [${dept.code}]?`)) {
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await deleteDepartment(dept.id);
      setFeedback(`Department "${dept.name}" deleted successfully.`);
      await loadDepartments();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete department.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      data-testid="department-modal"
    >
      <div className="relative bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-teal-50 text-teal-600 rounded-xl">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Department Management</h2>
              <p className="text-xs text-slate-500 font-medium">
                {facility.facility_name} ({facility.facility_code})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback / Error Banners */}
        {feedback && (
          <div
            className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between"
            data-testid="department-feedback-banner"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{feedback}</span>
            </div>
            <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {error && (
          <div
            className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between"
            data-testid="department-error-banner"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Action Bar */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Configured Departments ({departments.length})
          </span>
          {!isAdding && (
            <button
              onClick={() => setIsAdding(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
              data-testid="open-add-department-btn"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Department
            </button>
          )}
        </div>

        {/* Add Department Form */}
        {isAdding && (
          <form
            onSubmit={handleCreate}
            className="mb-5 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3"
            data-testid="add-department-form"
          >
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">New Department</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Department Code <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. DENTAL, PHYSIO"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                  className="w-full text-xs font-mono font-bold border border-slate-300 rounded-lg p-2 uppercase focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  data-testid="department-code-input"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Department Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dental Clinic"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  data-testid="department-name-input"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newActive}
                  onChange={(e) => setNewActive(e.target.checked)}
                  className="rounded text-teal-600 focus:ring-teal-500"
                  data-testid="department-active-checkbox"
                />
                Active Status
              </label>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsAdding(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-white border border-slate-200 rounded-lg transition"
                  data-testid="cancel-add-department-btn"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg transition disabled:opacity-50"
                  data-testid="submit-department-btn"
                >
                  {actionLoading ? 'Saving...' : 'Save Department'}
                </button>
              </div>
            </div>
          </form>
        )}

        {/* Department List */}
        {isLoading ? (
          <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
            Loading departments...
          </div>
        ) : departments.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400 bg-slate-50 border border-dashed border-slate-200 rounded-xl">
            No departments configured for this facility. Click "Add Department" above.
          </div>
        ) : (
          <div className="border border-slate-200 rounded-xl overflow-hidden" data-testid="departments-list">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Code</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.map((dept) => {
                  const isEditing = editingId === dept.id;
                  const codeKey = dept.code.toLowerCase();

                  return (
                    <tr
                      key={dept.id}
                      className="hover:bg-slate-50/50 transition"
                      data-testid={`department-row-${codeKey}`}
                    >
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-800">
                        <span className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200">
                          {dept.code}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-700 font-medium">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full text-xs border border-slate-300 rounded p-1 focus:ring-1 focus:ring-teal-500"
                            data-testid={`edit-dept-name-input-${codeKey}`}
                          />
                        ) : (
                          dept.name
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        {isEditing ? (
                          <label className="flex items-center gap-1.5 text-[11px] font-medium cursor-pointer">
                            <input
                              type="checkbox"
                              checked={editActive}
                              onChange={(e) => setEditActive(e.target.checked)}
                              className="rounded text-teal-600 focus:ring-teal-500"
                              data-testid={`edit-dept-active-checkbox-${codeKey}`}
                            />
                            {editActive ? 'Active' : 'Inactive'}
                          </label>
                        ) : (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              dept.is_active
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                : 'bg-slate-100 text-slate-600 border-slate-200'
                            }`}
                            data-testid={`department-status-${codeKey}`}
                          >
                            {dept.is_active ? 'Active' : 'Inactive'}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        {isEditing ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleSaveEdit(dept.id)}
                              disabled={actionLoading}
                              className="p-1 rounded text-emerald-600 hover:bg-emerald-50 transition"
                              title="Save"
                              data-testid={`save-edit-dept-btn-${codeKey}`}
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="p-1 rounded text-slate-400 hover:bg-slate-100 transition"
                              title="Cancel"
                              data-testid={`cancel-edit-dept-btn-${codeKey}`}
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleStartEdit(dept)}
                              className="p-1 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
                              title="Edit"
                              data-testid={`edit-department-btn-${codeKey}`}
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(dept)}
                              className="p-1 rounded text-rose-500 hover:text-rose-700 hover:bg-rose-50 transition"
                              title="Delete"
                              data-testid={`delete-department-btn-${codeKey}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end pt-4 border-t border-slate-100 mt-5">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DepartmentModal;
