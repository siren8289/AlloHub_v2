package com.allohub.screen.repository;

import com.allohub.screen.entity.CompanyScreen;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CompanyScreenRepository extends JpaRepository<CompanyScreen, Long> {

    List<CompanyScreen> findTop10ByOrderByIdDesc();
}
