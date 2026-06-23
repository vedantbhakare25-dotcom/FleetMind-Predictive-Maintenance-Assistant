function SHAPBarChart({ data = [] }) {
  return (
    <div className="shap-bar-chart">
      <h4>SHAP Importance</h4>
      <ul>
        {data.map((item) => (
          <li key={item.feature}>
            <span>{item.feature}</span>
            <div className="shap-bar-chart__bar">
              <div
                className="shap-bar-chart__fill"
                style={{ width: `${item.value}%` }}
              />
            </div>
            <strong>{item.value.toFixed(1)}%</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SHAPBarChart;
