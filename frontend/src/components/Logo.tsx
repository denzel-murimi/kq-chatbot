import Image from "next/image";

type Props = {
  className?: string;
  priority?: boolean;
};

// Full Kenya Airways wordmark ("The Pride of Africa"). Source is 800x187;
// size it by height or width via className and the other axis follows.
export function Logo({ className = "h-10 w-auto", priority = false }: Props) {
  return (
    <Image
      src="/kq-logo.png"
      alt="Kenya Airways — The Pride of Africa"
      width={800}
      height={187}
      priority={priority}
      className={className}
    />
  );
}
