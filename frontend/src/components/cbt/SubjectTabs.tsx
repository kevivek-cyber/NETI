import clsx from "clsx";

export type Subject = "PHYSICS" | "CHEMISTRY" | "BIOLOGY";

interface SubjectTabsProps {
  activeSubject: Subject;
  onSubjectChange: (subject: Subject) => void;
}

export function SubjectTabs({ activeSubject, onSubjectChange }: SubjectTabsProps) {
  const subjects: Subject[] = ["PHYSICS", "CHEMISTRY", "BIOLOGY"];

  return (
    <div className="subject-tabs-container">
      <div className="subject-tabs">
        {subjects.map((subj) => (
          <button
            key={subj}
            className={clsx("subject-tab", activeSubject === subj && "active")}
            onClick={() => onSubjectChange(subj)}
            aria-current={activeSubject === subj ? "page" : undefined}
          >
            {subj}
          </button>
        ))}
      </div>
    </div>
  );
}
