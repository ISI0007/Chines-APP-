import React from "react";
import { Protected } from "../components/StudyUI";
import LeaderboardScreen from "../screens/LeaderboardScreen";
export default function Leaderboard() { return <Protected><LeaderboardScreen /></Protected>; }
