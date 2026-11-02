import { Protected } from "../components/StudyUI";
import ProfileScreen from "../screens/ProfileScreen";

export default function ProfileRoute() {
  return <Protected><ProfileScreen /></Protected>;
}
