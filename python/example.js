/**
 * Continue JavaScript 분석 테스트 예시
 * Tree-sitter와 LSP 분석을 위한 다양한 JavaScript 구문 요소 포함
 */

// 상수
const VERSION = "1.0.0";
const MAX_RETRIES = 3;
const TIMEOUT = 30000;

// 전역 변수
let globalConfig = {
    debug: true,
    version: VERSION,
    features: ["tree_sitter", "lsp", "autocomplete"]
};

let results = [];

// 클래스 정의
class BaseAnalyzer {
    constructor(name) {
        this.analyzerName = name;
        this.results = [];
    }
    
    async analyze(filepath) {
        throw new Error("analyze 메서드를 구현해야 합니다");
    }
    
    getResults() {
        return [...this.results];
    }
}

class TreeSitterAnalyzer extends BaseAnalyzer {
    constructor() {
        super("TreeSitterAnalyzer");
        this.service = new TreeSitterService();
    }
    
    async analyze(filepath) {
        try {
            const fs = require('fs').promises;
            const content = await fs.readFile(filepath, 'utf8');
            const ast = await this.service.parseAST(content);
            const symbols = await this.service.extractSymbols(ast);
            
            return {
                filepath,
                nodeCount: ast.getNodeCount(),
                maxDepth: ast.getMaxDepth(),
                symbolCount: symbols.length,
                nodeTypes: this.service.getNodeTypes(ast)
            };
        } catch (error) {
            throw new AnalysisError(`파일 읽기 실패: ${error.message}`, 1001);
        }
    }
}

class LSPAnalyzer extends BaseAnalyzer {
    constructor() {
        super("LSPAnalyzer");
        this.service = new LSPService();
    }
    
    async analyze(filepath) {
        try {
            const symbols = await this.service.getDocumentSymbols(filepath);
            return {
                filepath,
                symbolCount: symbols.length,
                symbols: symbols.map(s => s.name)
            };
        } catch (error) {
            throw new AnalysisError(`LSP 분석 실패: ${error.message}`, 1002);
        }
    }
}

class ContinueAnalyzer {
    constructor(config = {}) {
        this.config = { ...globalConfig, ...config };
        this.treeSitterAnalyzer = new TreeSitterAnalyzer();
        this.lspAnalyzer = new LSPAnalyzer();
    }
    
    async initialize() {
        try {
            await this.treeSitterAnalyzer.service.initialize();
            await this.lspAnalyzer.service.initialize();
            console.log("Continue 분석기 초기화 완료");
        } catch (error) {
            throw new AnalysisError(`초기화 실패: ${error.message}`, 1001);
        }
    }
    
    async analyzeFile(filepath, analysisType = 'COMBINED') {
        try {
            const results = {
                filepath,
                analysisType,
                timestamp: new Date().toISOString(),
                config: this.config
            };
            
            if (analysisType === 'TREE_SITTER' || analysisType === 'COMBINED') {
                const treeSitterResult = await this.treeSitterAnalyzer.analyze(filepath);
                results.treeSitter = treeSitterResult;
            }
            
            if (analysisType === 'LSP' || analysisType === 'COMBINED') {
                const lspResult = await this.lspAnalyzer.analyze(filepath);
                results.lsp = lspResult;
            }
            
            return results;
        } catch (error) {
            throw new AnalysisError(`파일 분석 실패: ${error.message}`, 1002);
        }
    }
    
    async getCompletions(filepath, position) {
        try {
            return await this.lspAnalyzer.service.getCompletions(filepath, position);
        } catch (error) {
            console.error(`자동완성 실패: ${error.message}`);
            return [];
        }
    }
    
    async getContext(query, filepath) {
        try {
            return await this.lspAnalyzer.service.getContext(query, filepath);
        } catch (error) {
            console.error(`컨텍스트 제공 실패: ${error.message}`);
            return [];
        }
    }
}

// 열거형 (객체로 구현)
const AnalysisType = {
    TREE_SITTER: 'TREE_SITTER',
    LSP: 'LSP',
    COMBINED: 'COMBINED'
};

// 예외 클래스
class AnalysisError extends Error {
    constructor(message, code = 0) {
        super(message);
        this.name = 'AnalysisError';
        this.code = code;
    }
}

// 데이터 클래스
class AnalysisResult {
    constructor(filepath, nodeCount = 0, maxDepth = 0, symbolCount = 0, nodeTypes = {}) {
        this.filepath = filepath;
        this.nodeCount = nodeCount;
        this.maxDepth = maxDepth;
        this.symbolCount = symbolCount;
        this.nodeTypes = nodeTypes;
        this.symbols = [];
    }
    
    getFilepath() { return this.filepath; }
    getNodeCount() { return this.nodeCount; }
    getMaxDepth() { return this.maxDepth; }
    getSymbolCount() { return this.symbolCount; }
    getNodeTypes() { return this.nodeTypes; }
    getSymbols() { return this.symbols; }
}

// 인터페이스 (객체로 구현)
const Analyzer = {
    analyze: (filepath) => { throw new Error("구현 필요"); },
    getName: () => { throw new Error("구현 필요"); }
};

// 제네릭 클래스 (JavaScript에서는 타입 안전성이 제한적)
class ResultContainer {
    constructor(data, success = true, errorMessage = null) {
        this.data = data;
        this.success = success;
        this.errorMessage = errorMessage;
    }
    
    getData() { return this.data; }
    isSuccess() { return this.success; }
    getErrorMessage() { return this.errorMessage; }
}

// 유틸리티 함수들
function calculateComplexity(symbols) {
    return symbols.length * 2 + 10;
}

function formatResult(result) {
    return `파일: ${result.getFilepath()}, 노드: ${result.getNodeCount()}, 깊이: ${result.getMaxDepth()}, 심볼: ${result.getSymbolCount()}`;
}

// 화살표 함수와 고차 함수
const filterSymbols = (symbols, prefix) => 
    symbols.filter(s => s.name.startsWith(prefix)).map(s => s.name);

const printSymbols = (symbols) => 
    symbols.forEach(s => console.log(s));

// 비동기 함수들
async function testTreeSitterAnalysis() {
    console.log("=== Tree-sitter 분석 테스트 ===");
    
    try {
        const analyzer = new ContinueAnalyzer();
        await analyzer.initialize();
        
        const result = await analyzer.analyzeFile(__filename, AnalysisType.TREE_SITTER);
        console.log(`Tree-sitter 분석 결과: ${JSON.stringify(result, null, 2)}`);
        
        console.log("Tree-sitter 분석 테스트 완료\n");
    } catch (error) {
        console.error(`Tree-sitter 분석 테스트 실패: ${error.message} (코드: ${error.code})\n`);
    }
}

async function testLSPAnalysis() {
    console.log("=== LSP 분석 테스트 ===");
    
    try {
        const analyzer = new ContinueAnalyzer();
        await analyzer.initialize();
        
        const result = await analyzer.analyzeFile(__filename, AnalysisType.LSP);
        console.log(`LSP 분석 결과: ${JSON.stringify(result, null, 2)}`);
        
        console.log("LSP 분석 테스트 완료\n");
    } catch (error) {
        console.error(`LSP 분석 테스트 실패: ${error.message} (코드: ${error.code})\n`);
    }
}

async function testCombinedAnalysis() {
    console.log("=== 통합 분석 테스트 ===");
    
    try {
        const analyzer = new ContinueAnalyzer();
        await analyzer.initialize();
        
        const result = await analyzer.analyzeFile(__filename, AnalysisType.COMBINED);
        console.log(`통합 분석 결과: ${JSON.stringify(result, null, 2)}`);
        
        // 자동완성 테스트
        const position = { line: 50, character: 10 };
        const completions = await analyzer.getCompletions(__filename, position);
        console.log(`자동완성 항목 수: ${completions.length}`);
        
        // 컨텍스트 테스트
        const contextItems = await analyzer.getContext("function", __filename);
        console.log(`컨텍스트 항목 수: ${contextItems.length}`);
        
        console.log("통합 분석 테스트 완료\n");
    } catch (error) {
        console.error(`통합 분석 테스트 실패: ${error.message} (코드: ${error.code})\n`);
    }
}

// 메인 실행 함수
async function main() {
    console.log("Continue JavaScript 분석 테스트 시작");
    console.log("=".repeat(50));
    
    // 각종 분석 테스트 실행
    await testTreeSitterAnalysis();
    await testLSPAnalysis();
    await testCombinedAnalysis();
    
    console.log("모든 테스트 완료!");
}

// 모듈 내보내기 (Node.js 환경)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ContinueAnalyzer,
        AnalysisType,
        AnalysisError,
        AnalysisResult,
        testTreeSitterAnalysis,
        testLSPAnalysis,
        testCombinedAnalysis,
        main
    };
}

// 스크립트 실행
if (typeof require !== 'undefined' && require.main === module) {
    main().catch(error => {
        console.error("실행 중 오류 발생:", error);
        process.exit(1);
    });
}