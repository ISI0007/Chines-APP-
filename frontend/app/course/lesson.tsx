import { Protected } from "../../components/StudyUI";
import LessonScreen from "../../screens/LessonScreen";

export default function LessonRoute() {
  return <Protected><LessonScreen /></Protected>;
}
