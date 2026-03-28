<?php

class CsvManager {
    private $csvFile;
    private $headers = ['id', 'name', 'family_id', 'gender', 'is_driver', 'participation_count'];

    public function __construct($csvFile = null) {
        if ($csvFile === null) {
            $csvFile = __DIR__ . '/../data/list.csv';
        }
        $this->csvFile = $csvFile;
    }

    private function readCsv() {
        if (!file_exists($this->csvFile)) {
            return [];
        }

        $file = fopen($this->csvFile, 'r');
        if (!$file) return [];

        $data = [];
        $isFirst = true;
        while (($row = fgetcsv($file, 0, ',', '"', '\\')) !== false) {
            if ($isFirst) {
                // assume first row is header
                $isFirst = false;
                continue;
            }
            if (count($row) === count($this->headers)) {
                $data[] = array_combine($this->headers, $row);
            }
        }
        fclose($file);
        return $data;
    }

    private function writeCsv($data) {
        $file = fopen($this->csvFile, 'w');
        if (!$file) return false;

        fputcsv($file, $this->headers, ',', '"', '\\');
        foreach ($data as $row) {
            // Ensure data order matches header
            $out = [];
            foreach ($this->headers as $h) {
                $out[] = isset($row[$h]) ? $row[$h] : '';
            }
            fputcsv($file, $out, ',', '"', '\\');
        }
        fclose($file);
        return true;
    }

    public function getAll() {
        return $this->readCsv();
    }

    public function getByIds($ids) {
        $all = $this->getAll();
        $result = [];
        foreach ($all as $item) {
            if (in_array($item['id'], $ids)) {
                $result[] = $item;
            }
        }
        return $result;
    }

    public function add($item) {
        $data = $this->readCsv();
        // Generate new ID (simple max + 1)
        $maxId = 0;
        foreach ($data as $d) {
            if ((int)$d['id'] > $maxId) {
                $maxId = (int)$d['id'];
            }
        }
        $item['id'] = (string)($maxId + 1);
        $item['participation_count'] = isset($item['participation_count']) ? (string)$item['participation_count'] : '0';
        
        $data[] = $item;
        $this->writeCsv($data);
        return $item['id'];
    }

    public function update($id, $updateItem) {
        $data = $this->readCsv();
        $found = false;
        foreach ($data as &$d) {
            if ($d['id'] == $id) {
                foreach ($this->headers as $h) {
                    if ($h !== 'id' && isset($updateItem[$h])) {
                        $d[$h] = $updateItem[$h];
                    }
                }
                $found = true;
                break;
            }
        }
        if ($found) {
            $this->writeCsv($data);
        }
        return $found;
    }

    public function delete($id) {
        $data = $this->readCsv();
        $newData = [];
        $found = false;
        foreach ($data as $d) {
            if ($d['id'] != $id) {
                $newData[] = $d;
            } else {
                $found = true;
            }
        }
        if ($found) {
            $this->writeCsv($newData);
        }
        return $found;
    }

    public function incrementParticipationCounts($ids) {
        $data = $this->readCsv();
        foreach ($data as &$d) {
            if (in_array($d['id'], $ids)) {
                $d['participation_count'] = (string)((int)$d['participation_count'] + 1);
            }
        }
        $this->writeCsv($data);
    }
}
