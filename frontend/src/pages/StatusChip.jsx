// Status chip used across bank change requests. Colour AND label both
// convey status, so it never relies on colour alone.
export function StatusChip({ status }) {
  const styles = {
    Submitted: "bg-amber-50 text-amber-700 border-amber-200",
    Approved: "bg-green-50 text-green-700 border-green-200",
    Rejected: "bg-red-50 text-red-700 border-red-200",
    Returned: "bg-orange-50 text-orange-700 border-orange-200",
    Withdrawn: "bg-slate-100 text-slate-600 border-slate-200",
  };
  const style = styles[status] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded border ${style}`}>
      {status}
    </span>
  );
}
