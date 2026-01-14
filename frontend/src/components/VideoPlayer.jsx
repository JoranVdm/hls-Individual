import Hls from "hls.js";
import { useEffect, useRef } from "react";

export default function VideoPlayer({ episode }) {
  const videoRef = useRef(null);

useEffect(() => {
  const video = videoRef.current;
  const url = episode.playlist_path; // <-- this should already be full Supabase URL

  if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(url);
    hls.attachMedia(video);
  } else {
    video.src = url;
  }
}, [episode]);


  return <video ref={videoRef} controls className="w-full" />;
}
