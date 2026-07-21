export default function ChipToggle({ options, value, onChange, label }) {
  return (
    <div className="chip-toggle-wrap">
      {label ? <p>{label}</p> : null}
      <div className="chip-toggle" role="tablist" aria-label={label || "Field selector"}>
        {options.map((option) => {
          const isActive = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              className={`pick-btn${isActive ? " active" : ""}`}
              onClick={() => onChange(option.value)}
              role="tab"
              aria-selected={isActive}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}