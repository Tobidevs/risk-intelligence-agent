import Hero from "@/components/Hero";

export default function Home() {
  return (
    <main className="relative min-h-screen bg-bg-primary">
      {/* Faint dot-grid texture layer */}
      <div className="dot-grid pointer-events-none absolute inset-0" />

      {/* Content sits above the texture */}
      <div className="relative z-10">
        <Hero />
      </div>
    </main>
  );
}
