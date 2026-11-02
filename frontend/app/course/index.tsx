import { Protected } from "../../components/StudyUI";
import CourseScreen from "../../screens/CourseScreen";

export default function CourseRoute() {
  return <Protected><CourseScreen /></Protected>;
}
