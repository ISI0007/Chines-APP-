import React from "react";
import { Protected } from "../components/StudyUI";
import FlashcardScreen from "../screens/FlashcardScreen";
export default function Flashcards() { return <Protected><FlashcardScreen /></Protected>; }
