import java.util.concurrent.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Arrays;

public class QuantEngine {
    public static void main(String[] args) throws InterruptedException, ExecutionException {
        // We can scale this massively because of the compiled language and multithreading
        int totalPaths = 100000; 
        int days = 252;
        double startPrice = 400.0;
        double drift = 0.0005;
        double vol = 0.015;

        // 1. Hardware-Aware Sizing
        int availableCores = Runtime.getRuntime().availableProcessors();
        int pathsPerCore = totalPaths / availableCores;

        System.out.println("Spinning up Engine on " + availableCores + " distinct CPU cores.");

        // 2. The Thread Pool
        ExecutorService executor = Executors.newFixedThreadPool(availableCores);
        List<Future<double[]>> futures = new ArrayList<>();

        long startTime = System.nanoTime();

        // 3. Dispatching the Workload
        for (int i = 0; i < availableCores; i++) {
            Callable<double[]> worker = new MonteCarloWorker(pathsPerCore, days, startPrice, drift, vol);
            futures.add(executor.submit(worker)); // Hand the task to the pool and get a Future receipt
        }

        // 4. Memory-Contiguous Aggregation
        double[] allFinalPrices = new double[availableCores * pathsPerCore];
        int offset = 0;
        
        for (Future<double[]> future : futures) {
            // .get() pauses the orchestrator until this specific thread is finished computing
            double[] workerResult = future.get(); 
            
            // System.arraycopy is a blazing fast, low-level C memory block transfer
            System.arraycopy(workerResult, 0, allFinalPrices, offset, workerResult.length);
            offset += workerResult.length;
        }

        // Clean up the threads
        executor.shutdown();
        long endTime = System.nanoTime();

        System.out.println("Computed " + allFinalPrices.length + " paths in " + 
                           (endTime - startTime) / 1_000_000.0 + " milliseconds.");
        
        // From here, you would sort allFinalPrices to find the 5% VaR index
        Arrays.sort(allFinalPrices);
        System.out.println("5% VaR:" + allFinalPrices[5000]);
        System.out.println("Black_Swan_VaR_1_Percent": + allFinalPrices[1000]);
    }
}
