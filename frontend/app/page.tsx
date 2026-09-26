"use client";

import { useState } from "react";
import { DigitalTwinDashboard } from "@/components/DigitalTwinDashboard";
import { LandingPage } from "@/components/LandingPage";
import { ProcessingScreen } from "@/components/ProcessingScreen";
import { UploadDropzone } from "@/components/UploadDropzone";
import { askBurhan, createRun } from "@/lib/api";
import type { GroundedAnswer, TwinState } from "@/lib/types";

type ViewState = "landing" | "upload" | "processing" | "dashboard";

export default function Home() {
  const [view, setView] = useState<ViewState>("landing");
  const [files, setFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("Upload exactly five research papers from one focused domain to begin.");
  const [loading, setLoading] = useState(false);
  const [twin, setTwin] = useState<TwinState | null>(null);
  const [question, setQuestion] = useState("What is the most effective method?");
  const [answer, setAnswer] = useState<GroundedAnswer | null>(null);

  async function startRun() {
    setLoading(true);
    setProgress(18);
    setMessage("Uploading papers and starting scientific extraction.");
    setAnswer(null);
    setView("processing");

    try {
      const result = await createRun(files);
      setProgress(result.progress);
      setMessage(result.message);
      setTwin(result.twin);
      if (result.twin) {
        setView("dashboard");
      } else {
        setView("upload");
      }
    } catch (error) {
      setProgress(0);
      setMessage(error instanceof Error ? error.message : "Upload failed.");
      setView("upload");
    } finally {
      setLoading(false);
    }
  }

  async function submitQuestion() {
    if (!twin) return;
    setLoading(true);
    setMessage("Retrieving evidence and asking Burhan.");
    try {
      const result = await askBurhan(twin.run_id, question);
      setAnswer(result);
      setMessage("Grounded answer generated with supporting papers.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Question failed.");
    } finally {
      setLoading(false);
    }
  }

  if (view === "landing") {
    return <LandingPage onStart={() => setView("upload")} />;
  }

  if (view === "processing") {
    return <ProcessingScreen progress={progress} message={message} />;
  }

  if (view === "dashboard" && twin) {
    return <DigitalTwinDashboard twin={twin} question={question} answer={answer} loading={loading} onQuestionChange={setQuestion} onAsk={submitQuestion} />;
  }

  return <UploadDropzone files={files} loading={loading} message={message} onFilesChange={setFiles} onStart={startRun} />;
}
