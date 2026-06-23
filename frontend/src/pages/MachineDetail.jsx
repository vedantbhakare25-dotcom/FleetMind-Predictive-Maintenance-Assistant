import SHAPBarChart from "../components/SHAPBarChart";
import StatusBadge from "../components/StatusBadge";
import HealthGauge from "../components/HealthGauge";

function MachineDetail() {
  const machine = {
    id: "MACH-001",
    name: "Compressor A",
    status: "Healthy",
    health: 94,
    description:
      "Primary process compressor with normal vibration and temperature.",
  };

  const shapData = [
    { feature: "Temperature", value: 45.2 },
    { feature: "Vibration", value: 27.3 },
    { feature: "Pressure", value: 12.5 },
  ];

  return (
    <main className="machine-detail-page">
      <header>
        <h1>{machine.name}</h1>
        <StatusBadge status={machine.status} />
      </header>
      <section className="machine-detail__overview">
        <p>{machine.description}</p>
        <HealthGauge value={machine.health} />
      </section>
      <section className="machine-detail__insights">
        <h2>Failure drivers</h2>
        <SHAPBarChart data={shapData} />
      </section>
    </main>
  );
}

export default MachineDetail;
