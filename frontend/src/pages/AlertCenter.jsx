import AlertBanner from "../components/AlertBanner";

function AlertCenter() {
  const alerts = [
    {
      id: "A1",
      message: "Vibration above threshold for machine MACH-002.",
      type: "warning",
    },
    {
      id: "A2",
      message: "Firmware update recommended for machine MACH-004.",
      type: "info",
    },
  ];

  return (
    <main className="alert-center-page">
      <header>
        <h1>Alert Center</h1>
      </header>
      <section className="alert-list">
        {alerts.map((alert) => (
          <AlertBanner
            key={alert.id}
            message={alert.message}
            type={alert.type}
          />
        ))}
      </section>
    </main>
  );
}

export default AlertCenter;
