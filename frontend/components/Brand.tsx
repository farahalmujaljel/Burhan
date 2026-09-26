import Image from "next/image";

export function BrandLogo({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "relative h-10 w-28" : "relative h-14 w-44"}>
      <Image src="/brand/burhan-logo.png" alt="Burhan" fill sizes={compact ? "112px" : "176px"} className="object-contain object-left" priority />
    </div>
  );
}
