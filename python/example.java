package com.continue.analysis;

import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;
import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.time.format.*;

/**
 * Continue Java 분석 테스트 예시
 * Tree-sitter와 LSP 분석을 위한 다양한 Java 구문 요소 포함
 */
public class TestExample {
    
    // 상수
    private static final String VERSION = "1.0.0";
    private static final int MAX_RETRIES = 3;
    private static final Duration TIMEOUT = Duration.ofSeconds(30);
    
    // 정적 변수
    private static Map<String, Object> globalConfig = new HashMap<>();
    private static List<AnalysisResult> results = new ArrayList<>();
    
    // 인스턴스 변수
    private String name;
    private int id;
    private boolean active;
    private List<String> features;
    
    // 생성자
    public TestExample() {
        this.name = "Default";
        this.id = 0;
        this.active = true;
        this.features = new ArrayList<>();
    }
    
    public TestExample(String name, int id) {
        this.name = name;
        this.id = id;
        this.active = true;
        this.features = new ArrayList<>();
    }
    
    // 추상 클래스
    public static abstract class BaseAnalyzer {
        protected String analyzerName;
        protected List<AnalysisResult> results;
        
        public BaseAnalyzer(String name) {
            this.analyzerName = name;
            this.results = new ArrayList<>();
        }
        
        public abstract AnalysisResult analyze(String filepath) throws AnalysisException;
        
        public List<AnalysisResult> getResults() {
            return new ArrayList<>(results);
        }
    }
    
    // 구체 클래스
    public static class TreeSitterAnalyzer extends BaseAnalyzer {
        private TreeSitterService service;
        
        public TreeSitterAnalyzer() {
            super("TreeSitterAnalyzer");
            this.service = new TreeSitterService();
        }
        
        @Override
        public AnalysisResult analyze(String filepath) throws AnalysisException {
            try {
                String content = Files.readString(Paths.get(filepath));
                ASTNode ast = service.parseAST(content);
                List<Symbol> symbols = service.extractSymbols(ast);
                
                return new AnalysisResult(
                    filepath,
                    ast.getNodeCount(),
                    ast.getMaxDepth(),
                    symbols.size(),
                    service.getNodeTypes(ast)
                );
            } catch (IOException e) {
                throw new AnalysisException("파일 읽기 실패: " + e.getMessage(), 1001);
            }
        }
    }
    
    public static class LSPAnalyzer extends BaseAnalyzer {
        private LSPService service;
        
        public LSPAnalyzer() {
            super("LSPAnalyzer");
            this.service = new LSPService();
        }
        
        @Override
        public AnalysisResult analyze(String filepath) throws AnalysisException {
            try {
                List<DocumentSymbol> symbols = service.getDocumentSymbols(filepath);
                return new AnalysisResult(
                    filepath,
                    symbols.size(),
                    symbols.stream()
                        .map(s -> s.getName())
                        .collect(Collectors.toList())
                );
            } catch (Exception e) {
                throw new AnalysisException("LSP 분석 실패: " + e.getMessage(), 1002);
            }
        }
    }
    
    // 메인 클래스
    public static class ContinueAnalyzer {
        private TreeSitterAnalyzer treeSitterAnalyzer;
        private LSPAnalyzer lspAnalyzer;
        private Map<String, Object> config;
        
        public ContinueAnalyzer() {
            this.treeSitterAnalyzer = new TreeSitterAnalyzer();
            this.lspAnalyzer = new LSPAnalyzer();
            this.config = new HashMap<>();
            initializeConfig();
        }
        
        private void initializeConfig() {
            config.put("debug", true);
            config.put("version", VERSION);
            config.put("features", Arrays.asList("tree_sitter", "lsp", "autocomplete"));
        }
        
        public AnalysisResult analyzeFile(String filepath, AnalysisType type) throws AnalysisException {
            switch (type) {
                case TREE_SITTER:
                    return treeSitterAnalyzer.analyze(filepath);
                case LSP:
                    return lspAnalyzer.analyze(filepath);
                case COMBINED:
                    AnalysisResult treeSitterResult = treeSitterAnalyzer.analyze(filepath);
                    AnalysisResult lspResult = lspAnalyzer.analyze(filepath);
                    return combineResults(treeSitterResult, lspResult);
                default:
                    throw new AnalysisException("지원하지 않는 분석 타입: " + type, 1003);
            }
        }
        
        private AnalysisResult combineResults(AnalysisResult treeSitter, AnalysisResult lsp) {
            return new AnalysisResult(
                treeSitter.getFilepath(),
                treeSitter.getNodeCount() + lsp.getSymbolCount(),
                Math.max(treeSitter.getMaxDepth(), lsp.getMaxDepth()),
                treeSitter.getSymbolCount() + lsp.getSymbolCount(),
                new HashMap<>()
            );
        }
        
        public List<CompletionItem> getCompletions(String filepath, Position position) {
            try {
                return lspAnalyzer.service.getCompletions(filepath, position);
            } catch (Exception e) {
                System.err.println("자동완성 실패: " + e.getMessage());
                return new ArrayList<>();
            }
        }
        
        public List<ContextItem> getContext(String query, String filepath) {
            try {
                return lspAnalyzer.service.getContext(query, filepath);
            } catch (Exception e) {
                System.err.println("컨텍스트 제공 실패: " + e.getMessage());
                return new ArrayList<>();
            }
        }
    }
    
    // 열거형
    public enum AnalysisType {
        TREE_SITTER,
        LSP,
        COMBINED
    }
    
    // 예외 클래스
    public static class AnalysisException extends Exception {
        private int code;
        
        public AnalysisException(String message, int code) {
            super(message);
            this.code = code;
        }
        
        public int getCode() {
            return code;
        }
    }
    
    // 데이터 클래스
    public static class AnalysisResult {
        private String filepath;
        private int nodeCount;
        private int maxDepth;
        private int symbolCount;
        private Map<String, Integer> nodeTypes;
        private List<String> symbols;
        
        public AnalysisResult(String filepath, int nodeCount, int maxDepth, int symbolCount, Map<String, Integer> nodeTypes) {
            this.filepath = filepath;
            this.nodeCount = nodeCount;
            this.maxDepth = maxDepth;
            this.symbolCount = symbolCount;
            this.nodeTypes = nodeTypes;
            this.symbols = new ArrayList<>();
        }
        
        public AnalysisResult(String filepath, int symbolCount, List<String> symbols) {
            this.filepath = filepath;
            this.nodeCount = 0;
            this.maxDepth = 0;
            this.symbolCount = symbolCount;
            this.nodeTypes = new HashMap<>();
            this.symbols = symbols;
        }
        
        // Getters
        public String getFilepath() { return filepath; }
        public int getNodeCount() { return nodeCount; }
        public int getMaxDepth() { return maxDepth; }
        public int getSymbolCount() { return symbolCount; }
        public Map<String, Integer> getNodeTypes() { return nodeTypes; }
        public List<String> getSymbols() { return symbols; }
    }
    
    // 인터페이스
    public interface Analyzer {
        AnalysisResult analyze(String filepath) throws AnalysisException;
        String getName();
    }
    
    public interface Configurable {
        void setConfig(Map<String, Object> config);
        Map<String, Object> getConfig();
    }
    
    // 제네릭 클래스
    public static class ResultContainer<T> {
        private T data;
        private boolean success;
        private String errorMessage;
        
        public ResultContainer(T data) {
            this.data = data;
            this.success = true;
        }
        
        public ResultContainer(String errorMessage) {
            this.errorMessage = errorMessage;
            this.success = false;
        }
        
        public T getData() { return data; }
        public boolean isSuccess() { return success; }
        public String getErrorMessage() { return errorMessage; }
    }
    
    // 메인 메서드
    public static void main(String[] args) {
        System.out.println("Continue Java 분석 테스트 시작");
        System.out.println("=".repeat(50));
        
        try {
            ContinueAnalyzer analyzer = new ContinueAnalyzer();
            
            // 현재 파일 분석
            String currentFile = "TestExample.java";
            AnalysisResult result = analyzer.analyzeFile(currentFile, AnalysisType.COMBINED);
            
            System.out.println("분석 결과:");
            System.out.println("  파일: " + result.getFilepath());
            System.out.println("  노드 수: " + result.getNodeCount());
            System.out.println("  최대 깊이: " + result.getMaxDepth());
            System.out.println("  심볼 수: " + result.getSymbolCount());
            System.out.println("  노드 타입: " + result.getNodeTypes());
            
            // 자동완성 테스트
            Position position = new Position(50, 10);
            List<CompletionItem> completions = analyzer.getCompletions(currentFile, position);
            System.out.println("  자동완성 항목 수: " + completions.size());
            
            // 컨텍스트 테스트
            List<ContextItem> contextItems = analyzer.getContext("function", currentFile);
            System.out.println("  컨텍스트 항목 수: " + contextItems.size());
            
            System.out.println("모든 테스트 완료!");
            
        } catch (AnalysisException e) {
            System.err.println("분석 실패: " + e.getMessage() + " (코드: " + e.getCode() + ")");
        }
    }
    
    // 유틸리티 메서드들
    public static int calculateComplexity(List<Symbol> symbols) {
        return symbols.size() * 2 + 10;
    }
    
    public static String formatResult(AnalysisResult result) {
        return String.format(
            "파일: %s, 노드: %d, 깊이: %d, 심볼: %d",
            result.getFilepath(),
            result.getNodeCount(),
            result.getMaxDepth(),
            result.getSymbolCount()
        );
    }
    
    // 람다 표현식과 스트림 사용
    public static List<String> filterSymbols(List<Symbol> symbols, String prefix) {
        return symbols.stream()
            .filter(s -> s.getName().startsWith(prefix))
            .map(Symbol::getName)
            .collect(Collectors.toList());
    }
    
    // 메서드 참조 사용
    public static void printSymbols(List<Symbol> symbols) {
        symbols.forEach(System.out::println);
    }
}