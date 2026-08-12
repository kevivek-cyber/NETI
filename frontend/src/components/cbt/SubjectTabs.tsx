import clsx from "clsx";

export type Subject = "PHYSICS" | "CHEMISTRY" | "BIOLOGY";

interface SubjectTabsProps {
  activeSubject: Subject;
  onSubjectChange: (subject: Subject) => void;
}

const css = `
  .subj-tab-btn {
    background: transparent;
    color: #64748B;
    border: none;
    padding: 14px 24px;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    outline: none;
  }
  .subj-tab-btn:hover {
    color: #172A46;
  }
  .subj-tab-btn.active {
    color: #2563EB;
    border-bottom-color: #2563EB;
  }
`;

export function SubjectTabs({ activeSubject, onSubjectChange }: SubjectTabsProps) {
  const subjects: Subject[] = ["PHYSICS", "CHEMISTRY", "BIOLOGY"];

  return (
    <div style={{ display: 'flex', borderBottom: '1px solid #D9E2EF', background: '#FFFFFF', padding: '0 24px' }}>
      <style>{css}</style>
      {subjects.map((subj) => (
        <button
          key={subj}
          className={clsx("subj-tab-btn", activeSubject === subj && "active")}
          onClick={() => onSubjectChange(subj)}
          aria-current={activeSubject === subj ? "page" : undefined}
        >
          {subj}
        </button>
      ))}
    </div>
  );
}
