import { Protected } from "../components/StudyUI";
import WritingScreen from "../screens/WritingScreen";

export default function WritingRoute() {
  return (
    <Protected>
      <WritingScreen />
    </Protected>
  );
}
