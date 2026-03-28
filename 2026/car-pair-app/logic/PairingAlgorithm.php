<?php

class PairingAlgorithm {
    public function generate($members, $history) {
        $families = [];
        $totalPeople = count($members);
        $totalDrivers = 0;
        
        foreach ($members as $m) {
            $fid = $m['family_id'];
            if (!isset($families[$fid])) {
                $families[$fid] = [];
            }
            $families[$fid][] = $m;
            if ($m['is_driver'] == '1') {
                $totalDrivers++;
            }
        }
        
        $familyBlocks = array_values($families);
        
        $minCars = (int)ceil($totalPeople / 4);
        $maxCars = min($totalDrivers, $totalPeople); // bounded by drivers since each needs 1
        
        if ($minCars > $maxCars || $totalDrivers == 0) {
            return ['error' => 'ドライバーが不足しています。全員を乗せるための車を用意できません。'];
        }

        // Collect valid configs
        $validConfigs = [];
        
        // Try combinations of NumCars and AllowMultipleDrivers
        // We prefer NumCars equal to something that has 1 driver per car.
        
        for ($iter = 0; $iter < 100; $iter++) {
            shuffle($familyBlocks); // Randomize to find different solutions
            
            // We search over possible K cars
            $found_in_iter = false;
            for ($k = $minCars; $k <= $maxCars; $k++) {
                // strict: max 1 driver per car. (only if k >= totalDrivers)
                // Actually, if we have D drivers and K cars, if D > K we MUST have >1 driver in some car.
                // So strict mode is only possible if D <= K.
                $strictModePossible = ($totalDrivers <= $k);
                
                if ($strictModePossible) {
                    $res = $this->attemptPartition($familyBlocks, $k, false);
                    if ($res !== false) {
                        $validConfigs[] = $res;
                        $found_in_iter = true;
                        break;
                    }
                }
                
                // Fallback to allowing multiple drivers
                $res = $this->attemptPartition($familyBlocks, $k, true);
                if ($res !== false) {
                    $validConfigs[] = $res;
                    $found_in_iter = true;
                    break;
                }
            }
        }

        if (empty($validConfigs)) {
            return ['error' => '条件を満たす乗りあわせが見つかりませんでした。家族の人数やドライバーの数を確認してください。'];
        }

        // 絶対条件: 自動車の数はできるだけ少なくする
        $actualMinCars = PHP_INT_MAX;
        foreach ($validConfigs as $config) {
            $actualMinCars = min($actualMinCars, count($config));
        }
        
        $filteredConfigs = [];
        foreach ($validConfigs as $config) {
            if (count($config) === $actualMinCars) {
                $filteredConfigs[] = $config;
            }
        }

        // Score configs based on history & unformity
        $bestConfigs = [];
        $bestScore = PHP_INT_MAX;

        foreach ($filteredConfigs as $config) {
            $score = $this->calculateHistoryScore($config, $history);
            if ($score < $bestScore) {
                $bestScore = $score;
                $bestConfigs = [$config];
            } elseif ($score == $bestScore) {
                // To avoid duplicate identical configs in the array, we serialize and check
                $hash = $this->hashConfig($config);
                $isDuplicate = false;
                foreach ($bestConfigs as $bc) {
                    if ($this->hashConfig($bc) === $hash) {
                        $isDuplicate = true;
                        break;
                    }
                }
                if (!$isDuplicate) {
                    $bestConfigs[] = $config;
                }
            }
        }

        // Pick one randomly from the best to allow "Regenerate" to give different good options
        $chosen = $bestConfigs[array_rand($bestConfigs)];

        return [
            'success' => true,
            'cars' => $chosen,
            'score' => $bestScore
        ];
    }

    private function attemptPartition($blocks, $numCars, $allowMultipleDrivers) {
        $cars = array_fill(0, $numCars, []);
        return $this->backtrackPartition($cars, $blocks, 0, $allowMultipleDrivers);
    }

    private function backtrackPartition(&$cars, $blocks, $idx, $allowMultipleDrivers) {
        if ($idx == count($blocks)) {
            foreach ($cars as $car) {
                if (empty($car)) return false; 
                $driverCount = 0;
                $males = 0;
                $females = 0;
                $families_in_car = [];
                foreach ($car as $p) {
                    if ($p['is_driver'] == '1') $driverCount++;
                    if ($p['gender'] == 'M') $males++;
                    if ($p['gender'] == 'F') $females++;
                    $families_in_car[$p['family_id']] = true;
                }
                if ($driverCount < 1) return false;
                if (!$allowMultipleDrivers && $driverCount > 1) return false;
                if (count($car) == 2 && $males == 1 && $females == 1 && count($families_in_car) == 2) {
                    return false; 
                }
            }
            return $cars;
        }
        
        for ($c = 0; $c < count($cars); $c++) {
            if (count($cars[$c]) + count($blocks[$idx]) <= 4) {
                $originalCar = $cars[$c];
                $cars[$c] = array_merge($cars[$c], $blocks[$idx]);
                
                $res = $this->backtrackPartition($cars, $blocks, $idx + 1, $allowMultipleDrivers);
                if ($res !== false) return $res;
                
                $cars[$c] = $originalCar;
                
                if (empty($originalCar)) {
                    break; // symmetry breaking
                }
            }
        }
        return false;
    }

    private function calculateHistoryScore($config, $history) {
        $score = 0;
        $pastPairs = [];
        foreach ($history as $h) {
            if (!isset($h['cars'])) continue;
            foreach ($h['cars'] as $carIds) {
                $len = count($carIds);
                for ($i = 0; $i < $len; $i++) {
                    for ($j = $i + 1; $j < $len; $j++) {
                        $u = $carIds[$i]['id'];
                        $v = $carIds[$j]['id'];
                        if (strcmp($u, $v) > 0) { $temp = $u; $u = $v; $v = $temp; }
                        $key = "$u-$v";
                        if (!isset($pastPairs[$key])) $pastPairs[$key] = 0;
                        $pastPairs[$key]++;
                    }
                }
            }
        }
        
        $sizes = [];
        foreach ($config as $car) {
            $len = count($car);
            $sizes[] = $len;
            $familyIds = [];
            
            for ($i = 0; $i < $len; $i++) {
                $familyIds[$car[$i]['family_id']] = true;
                
                for ($j = $i + 1; $j < $len; $j++) {
                    $u = $car[$i]['id'];
                    $v = $car[$j]['id'];
                    if (strcmp($u, $v) > 0) { $temp = $u; $u = $v; $v = $temp; }
                    $key = "$u-$v";
                    if (isset($pastPairs[$key])) {
                        $score += $pastPairs[$key];
                    }
                }
            }
            
            // ペナルティ: 1人だけ、または、その家族だけの組
            if (count($familyIds) === 1) {
                $score += 50;
            }
        }

        // 乗車人数が不均等にならないように配慮 (人数の差分に強いペナルティ)
        if (!empty($sizes)) {
            $diff = max($sizes) - min($sizes);
            $score += ($diff * 200); 
        }

        return $score;
    }

    private function hashConfig($config) {
        $carHashes = [];
        foreach ($config as $car) {
            $ids = array_map(function($p) { return $p['id']; }, $car);
            sort($ids);
            $carHashes[] = implode(',', $ids);
        }
        sort($carHashes);
        return implode('|', $carHashes);
    }
}
