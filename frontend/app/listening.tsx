import { Protected } from "../components/StudyUI";
import ListeningTestScreen from "../screens/ListeningTestScreen";

export default function ListeningRoute() {
  return <Protected><ListeningTestScreen /></Protected>;
}
