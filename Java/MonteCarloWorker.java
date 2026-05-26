import java.util.concurrent.Callable;
import java.util.Random;

class MonteCarloWorker implements Callable<double[]> {
    private final int pathsToSimulate;
    private final int tradingDays;
    private final double initialPrice, drift, volatility;

    // The constructor sets the strict mathematical constraints for this specific thread
    public MonteCarloWorker(int paths, int days, double s0, double drift, double vol) {
        this.pathsToSimulate = paths;
        this.tradingDays = days;
        this.initialPrice = s0;
        this.drift = drift;
        this.volatility = vol;
    }

    @Override
    public double[] call() {
        // Thread-local random generation to prevent locking overhead
        Random rand = new Random(); 
        double[] finalPrices = new double[pathsToSimulate];
        
        for (int p = 0; p < pathsToSimulate; p++) {
            double currentPrice = initialPrice;
            
            // The pure mathematical engine: S_t = S_{t-1} * exp(drift + vol * Z)
            for (int d = 1; d < tradingDays; d++) {
                double z = rand.nextGaussian(); // Standard normal shock
                currentPrice *= Math.exp(drift + (volatility * z));
            }
            finalPrices[p] = currentPrice;
        }
        return finalPrices;
    }
}
