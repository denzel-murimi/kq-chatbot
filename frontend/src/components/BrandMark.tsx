type Props = {
  size?: "sm" | "lg";
};

export function BrandMark({ size = "lg" }: Props) {
  const sizing = size === "sm" ? "h-6 w-6 text-[10px]" : "h-10 w-10 text-xl";

  return (
    <div
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full bg-brand font-bold italic tracking-tighter text-white ${sizing}`}
    >
      KQ
    </div>
  );
}
