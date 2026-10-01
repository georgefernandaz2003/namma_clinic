import React from 'react';
import type { Facility, Visit } from '../../types';
import { Share2, CalendarCheck } from 'lucide-react';

interface ReferralFollowUpCardProps {
  visit: Visit;
  facilities: Facility[];
  orderReferral: boolean;
  setOrderReferral: (val: boolean) => void;
  destFacilityId: number | '';
  setDestFacilityId: (val: number | '') => void;
  referralUrgency: 'ROUTINE' | 'URGENT' | 'EMERGENCY';
  setReferralUrgency: (val: 'ROUTINE' | 'URGENT' | 'EMERGENCY') => void;
  referralReason: string;
  setReferralReason: (val: string) => void;
  scheduleFollowUp: boolean;
  setScheduleFollowUp: (val: boolean) => void;
  followUpDate: string;
  setFollowUpDate: (val: string) => void;
  followUpCategory: 'GENERAL' | 'NCD_ROUTINE' | 'POST_REFERRAL' | 'LAB_REVIEW';
  setFollowUpCategory: (val: 'GENERAL' | 'NCD_ROUTINE' | 'POST_REFERRAL' | 'LAB_REVIEW') => void;
  followUpInstructions: string;
  setFollowUpInstructions: (val: string) => void;
}

export const ReferralFollowUpCard: React.FC<ReferralFollowUpCardProps> = ({
  visit,
  facilities,
  orderReferral,
  setOrderReferral,
  destFacilityId,
  setDestFacilityId,
  referralUrgency,
  setReferralUrgency,
  referralReason,
  setReferralReason,
  scheduleFollowUp,
  setScheduleFollowUp,
  followUpDate,
  setFollowUpDate,
  followUpCategory,
  setFollowUpCategory,
  followUpInstructions,
  setFollowUpInstructions
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Referral Card */}
      <section aria-labelledby="referral-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <Share2 className="w-4 h-4 text-sky-600" aria-hidden="true" />
            <h2 id="referral-heading" className="text-sm font-bold text-slate-900">
              Secondary / Tertiary Referral
            </h2>
          </div>
          <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={orderReferral}
              onChange={(e) => setOrderReferral(e.target.checked)}
              className="rounded text-sky-600 focus:ring-sky-500 w-4 h-4 cursor-pointer"
            />
            <span>Refer Patient</span>
          </label>
        </div>

        {orderReferral && (
          <div className="space-y-3 text-xs">
            <div>
              <label htmlFor="ref-dest" className="block text-[11px] font-bold text-slate-700 mb-1">
                Destination Facility <span className="text-rose-500">*</span>
              </label>
              <select
                id="ref-dest"
                value={destFacilityId}
                onChange={(e) => setDestFacilityId(e.target.value ? Number(e.target.value) : '')}
                required={orderReferral}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600"
              >
                <option value="">-- Choose Referral Hospital --</option>
                {facilities
                  .filter((f) => f.id !== visit.facility)
                  .map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.facility_name} ({f.facility_type})
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label htmlFor="ref-urgency" className="block text-[11px] font-bold text-slate-700 mb-1">
                Referral Urgency
              </label>
              <select
                id="ref-urgency"
                value={referralUrgency}
                onChange={(e) => setReferralUrgency(e.target.value as 'ROUTINE' | 'URGENT' | 'EMERGENCY')}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600"
              >
                <option value="ROUTINE">Routine Specialist Opinion</option>
                <option value="URGENT">Urgent Secondary Review</option>
                <option value="EMERGENCY">Emergency Critical Transfer</option>
              </select>
            </div>

            <div>
              <label htmlFor="ref-reason" className="block text-[11px] font-bold text-slate-700 mb-1">
                Referral Reason <span className="text-rose-500">*</span>
              </label>
              <input
                id="ref-reason"
                type="text"
                value={referralReason}
                onChange={(e) => setReferralReason(e.target.value)}
                placeholder="e.g. Higher imaging / Ultrasound scan required"
                required={orderReferral}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600"
              />
            </div>
          </div>
        )}
      </section>

      {/* Follow-up Card */}
      <section aria-labelledby="followup-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <CalendarCheck className="w-4 h-4 text-emerald-600" aria-hidden="true" />
            <h2 id="followup-heading" className="text-sm font-bold text-slate-900">
              Follow-Up Schedule
            </h2>
          </div>
          <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={scheduleFollowUp}
              onChange={(e) => setScheduleFollowUp(e.target.checked)}
              className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
            />
            <span>Schedule Review</span>
          </label>
        </div>

        {scheduleFollowUp && (
          <div className="space-y-3 text-xs">
            <div>
              <label htmlFor="fu-date" className="block text-[11px] font-bold text-slate-700 mb-1">
                Follow-Up Due Date <span className="text-rose-500">*</span>
              </label>
              <input
                id="fu-date"
                type="date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                required={scheduleFollowUp}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              />
            </div>

            <div>
              <label htmlFor="fu-category" className="block text-[11px] font-bold text-slate-700 mb-1">
                Follow-Up Category
              </label>
              <select
                id="fu-category"
                value={followUpCategory}
                onChange={(e) => setFollowUpCategory(e.target.value as 'GENERAL' | 'NCD_ROUTINE' | 'POST_REFERRAL' | 'LAB_REVIEW')}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              >
                <option value="GENERAL">General Follow-Up</option>
                <option value="NCD_ROUTINE">NCD Longitudinal Review</option>
                <option value="LAB_REVIEW">Diagnostic Results Review</option>
                <option value="POST_REFERRAL">Post-Referral Check</option>
              </select>
            </div>

            <div>
              <label htmlFor="fu-instructions" className="block text-[11px] font-bold text-slate-700 mb-1">
                Clinical Instructions for Return Visit
              </label>
              <input
                id="fu-instructions"
                type="text"
                value={followUpInstructions}
                onChange={(e) => setFollowUpInstructions(e.target.value)}
                placeholder="e.g. Return in 7 days if fever persists"
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              />
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default ReferralFollowUpCard;
