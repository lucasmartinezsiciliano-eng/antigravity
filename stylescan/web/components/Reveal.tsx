"use client";

import { useEffect, useRef, useState, type ElementType, type CSSProperties, type ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  /** Stagger delay in ms */
  delay?: number;
  /** Travel distance in px */
  distance?: number;
  as?: ElementType;
  style?: CSSProperties;
  className?: string;
};

/**
 * Scroll-reveal wrapper. Fades + slides content up as it enters the viewport.
 *
 * Principle (impeccable): content is fully visible by default. The hidden
 * starting state is only applied once JS has armed the observer, so SSR,
 * no-JS, and headless renders never ship a blank section. Reduced-motion
 * users get the content instantly, no transition.
 */
export default function Reveal({
  children,
  delay = 0,
  distance = 16,
  as: Tag = "div",
  style,
  className,
}: RevealProps) {
  const ref = useRef<HTMLElement>(null);
  const [armed, setArmed] = useState(false);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(true);
      return;
    }

    setArmed(true);

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const animStyle: CSSProperties = armed
    ? {
        opacity: shown ? 1 : 0,
        transform: shown ? "none" : `translateY(${distance}px)`,
        transition: `opacity 0.6s var(--ease-out) ${delay}ms, transform 0.6s var(--ease-out) ${delay}ms`,
        willChange: shown ? "auto" : "transform, opacity",
      }
    : {};

  return (
    <Tag ref={ref} className={className} style={{ ...style, ...animStyle }}>
      {children}
    </Tag>
  );
}
