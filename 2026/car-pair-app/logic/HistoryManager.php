<?php
class HistoryManager {
    private $historyFile;

    public function __construct($historyFile = null) {
        if ($historyFile === null) {
            $historyFile = __DIR__ . '/../data/history.json';
        }
        $this->historyFile = $historyFile;
    }

    public function getHistory() {
        if (!file_exists($this->historyFile)) {
            return [];
        }
        $json = file_get_contents($this->historyFile);
        $data = json_decode($json, true);
        return is_array($data) ? $data : [];
    }

    public function addHistory($pairingData) {
        $history = $this->getHistory();
        $history[] = [
            'date' => date('Y-m-d H:i:s'),
            'cars' => $pairingData // array of cars, each car is an array of IDs
        ];
        file_put_contents($this->historyFile, json_encode($history, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }
}
