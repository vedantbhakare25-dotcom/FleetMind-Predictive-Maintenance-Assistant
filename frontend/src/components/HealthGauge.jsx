function HealthGauge({ value }) {
  const normalized = Math.min(100, Math.max(0, value));
  return (
    <div className="health-gauge">
      <div className="health-gauge__bar">
        <div
          className="health-gauge__fill"
          style={{ width: `${normalized}%` }}
        />
      </div>
      <span>{normalized}% health</span>
    </div>
  );
}

export default HealthGauge;
