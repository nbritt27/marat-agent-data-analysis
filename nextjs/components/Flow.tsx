import {useState, useRef, useEffect, useCallback, memo} from "react";
import Dagre from '@dagrejs/dagre';
import { Button } from "@/components/ui/button";
import {sendReportRequest} from '@/lib/data';
import { saveAs } from 'file-saver';
import './Flow.css';

import {
  Background,
  Controls,
  MiniMap,
  getNodesBounds,
  getViewportForBounds,
  ReactFlow,
  addEdge,
  Panel,
  useReactFlow,
  BackgroundVariant,
  useNodesState,
  applyNodeChanges,
  useOnSelectionChange,
  Connection,
  Node,
  Edge,
  applyEdgeChanges,
  useUpdateNodeInternals,
  useEdgesState,
  type OnConnect,
  ReactFlowProvider,
} from "@xyflow/react";
import { toSvg } from 'html-to-image';

import "@xyflow/react/dist/style.css";
import ChatResponseNodes from "@/components/nodes/ChatResponseNodes";
import ChatResponseNode from "@/components/nodes/ChatResponseNodes";
interface Elements {
  nodes: []; // Replace NodeType with the actual type for nodes
  edges: []; // Replace EdgeType with the actual type for edges
}
interface FlowProps {
  initialElements: Elements; // Replace `Element[]` with the actual type of `initialElements`
}

const nodeTypes={
  chatResponse: ChatResponseNodes
};
const getLayoutedElements = (nodes, edges, options) => {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: options.direction });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    }),
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;

      return { ...node, position: { x, y } };
    }),
    edges,
  };
};

const Flow=memo(({ initialElements }: FlowProps)=> {
  const reactFlowWrapper=useRef(null);
  const { fitView } = useReactFlow();

  const [nodes, setNodes] = useNodesState([]);
  const [edges, setEdges] = useEdgesState([]);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const saveFlow = () => {
    const flow = {
      nodes,
      edges,
      selectedNodes,
    };
    localStorage.setItem('flow', JSON.stringify(flow));
  };
  
  useEffect(() => {
    const savedFlow = localStorage.getItem('flow');
    if (savedFlow) {
      const { nodes: savedNodes, edges: savedEdges, selectedNodes: savedSelectedNodes} = JSON.parse(savedFlow);
      setNodes(savedNodes);
      setEdges(savedEdges);
      setSelectedNodes(savedSelectedNodes);
    }
    setNodes((prevNodes) => {
      const existingNodeIds = prevNodes.map((node) => node.id);
      const newNodes = initialElements.nodes.filter(
        (node) => !existingNodeIds.includes((node as Node).id)
      );
      return [...prevNodes, ...newNodes];
    });
    setEdges((prevEdges) => {
      const existingEdgeIds = prevEdges.map((edge) => edge.id);
      const newEdges = initialElements.edges.filter(
        (edge) => !existingEdgeIds.includes((edge as Edge).id)
      );
      return [...prevEdges, ...newEdges];
    });
  }, [initialElements]);
  const onLayout = useCallback(
    (direction) => {
      console.log(nodes);
      const layouted = getLayoutedElements(nodes, edges, { direction });

      setNodes([...layouted.nodes]);
      setEdges([...layouted.edges]);

      window.requestAnimationFrame(() => {
        fitView();
      });
    },
    [nodes, edges],
  );
  const onConnect = useCallback(
    (params) =>
      setEdges((eds) =>
        addEdge(params, eds),
      ),
    [],
  );
  
  const onNodesChange = useCallback(
    (changes) => {
      setNodes((nds) => applyNodeChanges(changes, nds));
      const selected = changes.filter((change) => change.selected).map((change) => change.id);
      
    },
    [setNodes]
  );
  const getNodeStyles = useCallback(
    (node) => ({
      ...node.style,
      backgroundColor: node.selected ? '#f0f0f0' : 'white', // Set light gray for selected nodes

    }),
    []
  );

  useEffect(() => {
    saveFlow();
  }, [nodes, edges, selectedNodes]);
  const nodesWithStyles = nodes.map((node) => ({
    ...node,
    style: getNodeStyles(node),
  }));

  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const selectionChange=useCallback(({nodes,edges})=>{
    const selectedIds=nodes.map((node)=>node.id);
    console.log(selectedIds);
    setSelectedNodes(selectedIds);
  },[]);
  useOnSelectionChange({
    onChange: useCallback(({nodes,edges})=>{
      const selectedIds=nodes.map((node)=>node.id);
      console.log(selectedIds);
      setSelectedNodes(selectedIds);
    },[selectedNodes])
  });

  const handleSelectAll = () => {
    const allNodesSelected = nodes.map(node => ({
      ...node,
      selected: true,
    }));
    setNodes(allNodesSelected);
  };
  const downloadImage=(dataUrl:any) =>{
    const a = document.createElement('a');
  
    a.setAttribute('download', 'flow.svg');
    
    a.setAttribute('href', dataUrl);
    a.click();
  };
  const exportToSVG = () => {
    const nodesBounds = getNodesBounds(nodes);
    const viewport = getViewportForBounds(
      nodesBounds,
      2500,
      1000,
      0.5,
      2,
      1
    );

    toSvg(document.querySelector('.react-flow__viewport') as HTMLElement, {
      
    }).then(downloadImage);
  };
  
  return (
<ReactFlowProvider>
  <div style={{ height: '85vh', width: '100%', position: 'relative' }} ref={reactFlowWrapper}>
  <ReactFlow
    nodes={nodesWithStyles}
    edges={edges}
    onNodesChange={onNodesChange}
    onEdgesChange={onEdgesChange}
    onSelectionChange={selectionChange}
    onConnect={onConnect}
    nodeTypes={nodeTypes}
    snapToGrid={true}
    snapGrid={[20,20]}
    fitView
    attributionPosition="bottom-left"
    // selectable={true}
  >
    <Panel position="top-right">
      <Button className="flowButton exclude-in-svg" onClick={handleSelectAll}>Select All</Button>
      <Button className="flowButton" onClick={() => onLayout('TB')}>vertical layout</Button>
      <Button className="flowButton" onClick={() => onLayout('LR')}>horizontal layout</Button>
    </Panel>
    <Background variant={BackgroundVariant.Dots} />

    <MiniMap
    />
    <Controls />
    <Panel position="bottom-center">
    <Button className="flowButton" onClick={()=>sendReportRequest({selectedNodes})}>
      Generate Review From Selected Nodes
    </Button>
    <Button className="flowButton " onClick={exportToSVG}>
      Export as SVG
    </Button>
    </Panel>
  </ReactFlow>
  </div>
 
</ReactFlowProvider>

      );
    

});
export default function({initialElements}){
  return (
    <ReactFlowProvider>
      <Flow initialElements={initialElements}/>
    </ReactFlowProvider>
  )
};