export function BackgroundMesh() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      {/* Indigo blob — top right */}
      <div
        className="absolute -top-1/4 -right-1/4 h-[600px] w-[600px] rounded-full opacity-[0.07]"
        style={{
          background:
            "radial-gradient(circle, #818cf8 0%, transparent 70%)",
          animation: "mesh-drift 20s ease-in-out infinite",
        }}
      />
      {/* Zinc blob — bottom left */}
      <div
        className="absolute -bottom-1/4 -left-1/4 h-[500px] w-[500px] rounded-full opacity-[0.05]"
        style={{
          background:
            "radial-gradient(circle, #a1a1aa 0%, transparent 70%)",
          animation: "mesh-drift 25s ease-in-out infinite reverse",
        }}
      />
    </div>
  );
}
