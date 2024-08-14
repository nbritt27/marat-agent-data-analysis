'use client'
import React, {memo} from 'react'
import type {Node} from "@xyflow/react";
import { Handle, Position, NodeResizeControl, useUpdateNodeInternals} from "@xyflow/react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })

import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {Accordion, AccordionItem} from "@nextui-org/accordion";

export type ChatResponseData = {
  content?: [];
};

export type ChatResponseNode = Node<ChatResponseData>;

const renderContent = (contentArray) => {
  console.log(contentArray)
  return contentArray.map((item: { type: any; content:any }, index: React.Key | null | undefined) => {
    console.log(item)
    switch (item.type) {
      case 'text':
        return <p key={index} className="chat-content">{item.content}</p>;
      case 'plotly':
        return (
          <div key={index} className="plotly-container">
            <Plot
              data={item.content.data}
              layout={{...item.content.layout,autosize: true}}
              config={item.content.config || {}}
            />
          </div>
        );
      case "html":
        return <div dangerouslySetInnerHTML={{__html: item.content}}/>
      case 'markdown':
        return <Markdown remarkPlugins={[remarkGfm]} key={index} className="chat-content">{item.content}</Markdown>;
      case 'theme':
        return <h2 key={index} className="chat-content">{item.content}</h2>;
      case "code":
        return (
          <Accordion isCompact>
            <AccordionItem key="1" aria-label="Show Code" title="Show Code">
              <Markdown remarkPlugins={[remarkGfm]} key={index} className="chat-content">{item.content}</Markdown>;

            </AccordionItem>

          </Accordion>
        );
      default:
        return <p key={index} className="chat-content">Unsupported content type</p>;
    }
  });
  
};

const controlStyle = {
  background: 'transparent',
  border: 'none',
};
function ResizeIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      strokeWidth="2"
      stroke="#ff0071"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ position: 'absolute', right: 5, bottom: 5 }}
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <polyline points="16 20 20 20 20 16" />
      <line x1="14" y1="14" x2="20" y2="20" />
      <polyline points="8 4 4 4 4 8" />
      <line x1="4" y1="4" x2="10" y2="10" />
    </svg>
  );
}
interface NodeInputProp{
  data:any;
  isConnectable:boolean;
}
export default memo(({data, isConnectable}:NodeInputProp)=>{
  const updateNodeInternals = useUpdateNodeInternals();

  console.log(data)

  return (
    <>
      <NodeResizeControl style={controlStyle} minWidth={100} minHeight={50}>
        <ResizeIcon />
      </NodeResizeControl>


      <div className="chat-card">  
      <div className={data.content.category}>

      {renderContent(data.content)}

      </div>

      </div>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#555' }}
        onConnect={(params) => console.log('handle onConnect', params)}
        id="left"   
        />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="top"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
      />
    </>
  );
});
