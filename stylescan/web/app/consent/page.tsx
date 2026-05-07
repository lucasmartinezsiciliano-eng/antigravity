"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ConsentRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/checkout"); }, [router]);
  return null;
}
