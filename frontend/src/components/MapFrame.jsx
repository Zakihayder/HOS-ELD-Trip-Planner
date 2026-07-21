export default function MapFrame({ children, compact = false }) {
  return <div className={`map-frame${compact ? " compact" : ""}`}>{children}</div>;
}