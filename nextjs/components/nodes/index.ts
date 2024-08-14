import type { BuiltInNode, Node, NodeTypes } from "@xyflow/react";
import ChatResponseNode, {
  type ChatResponseNode as ChatResponseNodeType,
} from "./ChatResponseNodes";

export const initialNodes = [
  // { id: "a", type: "input", position: { x: 0, y: 0 }, data: { label: "wire" } },
  {
    id: "b",
    type: "chat-response",
    position: { x: -100, y: 100 },
    data: { content: [{type: "markdown", content: "hello"}] },
  },
  // { id: "c", position: { x: 100, y: 100 }, data: { label: "your ideas" } },
  // {
  //   id: "d",
  //   type: "output",
  //   position: { x: 0, y: 200 },
  //   data: { label: "with React Flow" },
  // },
] satisfies Node[];

export const nodeTypes = {
  "chat-response": ChatResponseNode,
  // Add any of your custom nodes here!
} satisfies NodeTypes;

// Append the types of you custom edges to the BuiltInNode type
export type CustomNodeType = BuiltInNode | ChatResponseNodeType;
