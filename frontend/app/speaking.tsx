import { Protected } from "../components/StudyUI";
import SpeakingScreen from "../screens/SpeakingScreen";

export default function SpeakingRoute() {
  return <Protected><SpeakingScreen /></Protected>;
}
