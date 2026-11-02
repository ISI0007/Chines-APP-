import { Protected } from "../components/StudyUI";
import ProgressionScreen from "../screens/ProgressionScreen";

export default function ProgressionRoute() {
  return <Protected><ProgressionScreen /></Protected>;
}
