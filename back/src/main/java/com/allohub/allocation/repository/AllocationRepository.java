package com.allohub.allocation.repository;

import com.allohub.allocation.entity.Allocation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AllocationRepository extends JpaRepository<Allocation, Long> {

    List<Allocation> findTop10ByOrderByIdDesc();
}
