/**
 * 원본 Continue 프로젝트에서 파일 분석하는 스크립트
 * Python 구현과 동일한 결과를 제공합니다.
 */

import fs from "node:fs";
import path from "node:path";
import { getAst } from "./core/autocomplete/util/ast.js";
import { getSymbolsForFile } from "./core/util/treeSitter.js";

// 노드 수 계산 함수
function countNodes(node: any): number {
  if (!node) return 0;
  let count = 1;
  if (node.children) {
    for (const child of node.children) {
      count += countNodes(child);
    }
  }
  return count;
}

// 최대 깊이 계산 함수
function getMaxDepth(node: any, depth: number = 0): number {
  if (!node || !node.children || node.children.length === 0) {
    return depth;
  }
  
  let maxChildDepth = depth;
  for (const child of node.children) {
    const childDepth = getMaxDepth(child, depth + 1);
    maxChildDepth = Math.max(maxChildDepth, childDepth);
  }
  
  return maxChildDepth;
}

// 노드 타입별 개수 계산 함수
function getNodeTypes(node: any): Record<string, number> {
  const types: Record<string, number> = {};
  
  function countTypes(currentNode: any) {
    if (!currentNode) return;
    
    const nodeType = currentNode.type;
    types[nodeType] = (types[nodeType] || 0) + 1;
    
    if (currentNode.children) {
      for (const child of currentNode.children) {
        countTypes(child);
      }
    }
  }
  
  countTypes(node);
  return types;
}

// 파일 분석 함수
async function analyzeFile(filepath: string): Promise<any> {
  try {
    // 파일 내용 읽기
    const contents = await fs.promises.readFile(filepath, "utf8");
    
    // AST 분석
    const ast = await getAst(filepath, contents);
    
    // 심볼 추출
    const symbols = await getSymbolsForFile(filepath, contents);
    
    // 언어 결정
    const ext = path.extname(filepath).toLowerCase();
    const languageMap: Record<string, string> = {
      '.py': 'python',
      '.java': 'java',
      '.js': 'javascript',
      '.jsx': 'javascript',
      '.ts': 'javascript',
      '.tsx': 'javascript'
    };
    const language = languageMap[ext] || 'unknown';
    
    // 결과 구성
    const result = {
      filepath,
      language,
      ast_root: {
        type: ast?.rootNode.type || "module",
        text: ast?.rootNode.text ? 
          (ast.rootNode.text.length > 100 ? 
            ast.rootNode.text.substring(0, 100) + "..." : 
            ast.rootNode.text) : "",
        start_position: [
          ast?.rootNode.startPosition.row || 0, 
          ast?.rootNode.startPosition.column || 0
        ],
        end_position: [
          ast?.rootNode.endPosition.row || 0, 
          ast?.rootNode.endPosition.column || 0
        ],
        children_count: ast?.rootNode.children?.length || 0
      },
      symbols: symbols || [],
      analysis: {
        total_nodes: countNodes(ast?.rootNode),
        max_depth: getMaxDepth(ast?.rootNode),
        node_types: getNodeTypes(ast?.rootNode)
      }
    };
    
    return result;
    
  } catch (error) {
    return {
      error: `분석 중 오류 발생: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

// 메인 실행 함수
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error("사용법: npx ts-node analyze-file.ts <파일경로> [출력파일]");
    console.error("예시: npx ts-node analyze-file.ts test_example.py result.json");
    process.exit(1);
  }
  
  const filepath = args[0];
  const outputFile = args[1];
  
  // 파일 존재 확인
  if (!fs.existsSync(filepath)) {
    console.error(`파일을 찾을 수 없습니다: ${filepath}`);
    process.exit(1);
  }
  
  console.log(`분석 중: ${filepath}`);
  
  // 파일 분석
  const result = await analyzeFile(filepath);
  
  // 결과 출력
  const jsonResult = JSON.stringify(result, null, 2);
  
  if (outputFile) {
    // 파일로 저장
    await fs.promises.writeFile(outputFile, jsonResult, "utf8");
    console.log(`결과가 저장되었습니다: ${outputFile}`);
  } else {
    // 콘솔에 출력
    console.log(jsonResult);
  }
}

// 스크립트 실행
if (require.main === module) {
  main().catch(error => {
    console.error("실행 중 오류 발생:", error);
    process.exit(1);
  });
}

export { analyzeFile };
