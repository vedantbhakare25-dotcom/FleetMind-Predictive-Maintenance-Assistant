function AlertBanner({ message, type = "info" }) {
  return (
    <div className={`alert-banner alert-banner--${type}`}>
      <p>{message}</p>
    </div>
  );
}

export default AlertBanner;
